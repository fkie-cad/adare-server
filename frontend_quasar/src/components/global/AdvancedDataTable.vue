<template>
  <div
    class="tw-w-5/6"
  >
  <q-table
    :title="title"
    :rows="rows"
    :columns="columns"
    row-key="name"
    :visible-columns="m_visibleColumns"
    class="tw-w-full"
  >
    <template v-slot:header="props">
      <q-tr :props="props">
        <q-th
          v-for="col in props.cols"
          :key="col.name"
          :props="props"
        >
          {{ col.label }}
        </q-th>
      </q-tr>
      <q-tr :props="props" v-if="filter_row">
        <q-td
          v-for="col in props.cols"
          :key="col.name"
          :props="props"
          style="border-bottom-width: 1px"
        >
          <q-input
            outlined
            dense
            :label="'filter: '+col.label"
            v-model="filter_strings_by_columns[col.field]"
            @update:model-value="applyFilter()"
            :disable="col.disbale_filter"
          />
        </q-td>
      </q-tr>
    </template>
    <template v-slot:top="props">
      <q-btn
        flat round dense
        :icon="props.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
        @click="props.toggleFullscreen"
      />

      <div class="col-2 q-table__title q-ml-md">{{ title }}</div>
      <q-space />
      <q-btn
        icon="filter_list"
        color="primary"
        class="q-mr-md"
        v-if="data_filter_function"
        @click="filter_row = !filter_row"
      />
      <q-btn
        icon="settings"
        color="primary"
      >
        <q-menu
          anchor="bottom right"
          self="top right"
        >
          <q-list
            dense
          >
            <q-item>
              <q-checkbox
                v-model="show_all"
                label="show all"
                @update:model-value="showAll()"
              />
              <q-checkbox
                v-model="hide_all"
                label="hide all"
                @update:model-value="hideAll()"
              />
            </q-item>
            <q-separator />
            <q-item
              v-for="col in m_hideableColumns"
              :key="col.field"
            >
              <q-checkbox v-model="m_visibleColumns" :val=col.field :label="col.label" @update:model-value="AdjustShowHideAll()"/>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>

    </template>
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td
          v-for="col in props.cols"
          :key="col.field"
        >
          <div
            v-if="col.type=='user_icon'"
          >
            <ProfileImage
              :username=col.value
              size="md"
              :tooltip=true
              :linktoprofile=true
              v-if=col.value
            />
          </div>
          <div v-else-if="col.type=='link'">
            <router-link :to="col.link_url+props.row[col.link_field]">
              <q-icon
                :name="col.link_icon"
                size="32px"
                color="secondary"
              />
            </router-link>
          </div>
          <div v-else-if="col.type=='tags'">
            <q-badge v-for="item in col.value" :key="item" color="primary" class="q-ma-sm">
              #{{ item }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='status'">
            <q-icon
              name="check_circle"
              color="positive"
              v-if="col.value.name == 'success'"
              size="32px"
            />
            <q-icon
              name="cancel"
              color="negative"
              v-if="col.value.name == 'failed'"
              size="32px"
            />
          </div>
          <div v-else-if="col.type=='run_counts'">
            <q-badge color="positive" class="q-ma-sm">
              {{ col.value.successful }}
            </q-badge>
            <q-badge color="negative" class="q-ma-sm">
              {{ col.value.failed }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='testfunction'">
            {{ col.value.name }}
          </div>
          <div v-else-if="col.type=='subparameter'">
            <div v-if="col.value">
              {{ col.value[col.subparameter] }}
            </div>
          </div>
          <div v-else-if="col.type=='os_info'">
            {{ col.value.os }} {{ col.value.version }}
          </div>
          <div v-else-if="col.type=='download'">
            <q-btn
              color="primary"
              icon="get_app"
              @click="DownloadFile(col.value, col.filename)"
              v-if="col.filename"
            />
            <q-btn
              color="primary"
              icon="get_app"
              @click="DownloadFile(col.value, col.filename_function(props.row))"
              v-else
            />
          </div>
          <div v-else-if="col.type=='expand'">
            <q-btn size="sm" color="secondary" round dense @click="props.expand = !props.expand; expand_column=col.field" :icon="props.expand ? 'arrow_upward' : 'arrow_downward'" />
          </div>
          <div v-else-if="col.type=='testparameterentry'">
            <q-markup-table
              dense
            >
              <tbody>
                <tr v-for="item in col.value" :key="item.parameter.name">
                  <td>{{ item.parameter.name }}</td>
                  <td class="tw-text-right">{{ item.value }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </div>
          <div v-else>
            {{ col.value }}
          </div>
        </q-td>
      </q-tr>
      <q-tr v-show="props.expand" :props="props">
          <q-td colspan="100%">
            <q-markup-table
              dense
              bordered
            >
              <thead>
                <q-tr class="tw-bg-blue-900 text-white">
                  <q-th><div>Parameter</div></q-th>
                  <q-th><div>Value</div></q-th>
                  <q-th><div>Description</div></q-th>
                </q-tr>
              </thead>
              <tbody>
                <q-tr v-for="item in props.row[expand_column]" :key="item.name">
                  <q-td><div>{{ item.name }}</div></q-td>
                  <q-td><div>{{ item.dtype }}</div></q-td>
                  <q-td><div class="tw-whitespace-pre-wrap">{{ item.description }}</div></q-td>
                </q-tr>
              </tbody>
            </q-markup-table>
          </q-td>
      </q-tr>
    </template>
  </q-table>
  </div>
</template>

<script lang="ts">
import {onMounted, ref} from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import {hideableColumnEntry, ColumnEntry} from 'src/datatypes/advancedtable';
import axios from 'axios';
import { exportFile } from 'quasar';

export default {
  name: 'AdvancedDataTable',
  components: {ProfileImage},

  props: {
    columns: {
      type: Array,
      required: true,
    },
    visibleColumns: {
      type: Array,
      required: false,
    },
    title: {
      type: String,
      required: false,
      default: '',
    },
    data_load_function: {
      type: Function,
      required: false,
    },
    data_get_function: {
      type: Function,
      required: true,
    },
    data_filter_function: {
      type: Function,
      required: false,
    }
  },

  setup(props) {
    let rows = ref([])
    let m_columns = ref<ColumnEntry[]>([])
    let m_visibleColumns = ref<string[]>([])
    let m_hideableColumns = ref<hideableColumnEntry[]>([])
    let m_nonHideableColumns = ref<ColumnEntry[]>([])
    let filter_row = ref(false);
    let api_filter_string = ''

    let filter_strings_by_columns: any = ref({})
    let filter_strings_total = ref('')

    let show_all = ref(false)
    let hide_all = ref(false)

    let expand_column = ref('')

    onMounted(async () => {
      m_columns.value = props.columns
      // setup hideable columns
      // get column field and label form props.columns
      for (let column of m_columns.value) {
        // add column to hideable columns if hideable property is set
        if (column.hideable) {
          m_hideableColumns.value.push(column)
        } else {
          m_nonHideableColumns.value.push(column)
        }
      }
      // set visible columns
      if (props.visibleColumns) {
        m_visibleColumns.value = props.visibleColumns as string[]
      } else {
        // if no visible columns are set, set all columns to visible
        for (let column of m_columns.value) {
          m_visibleColumns.value.push(column.field)
        }
      }
      // setup filter strings
      filter_strings_by_columns.value = Object.keys(props.columns)
      // initialize all values to empty string
      for (let column of m_columns.value) {
        filter_strings_by_columns.value[column.field] = ''
      }
      // load rows of table
      await loadTableData()
      AdjustShowHideAll()
    })

    async function loadTableData(){
      if (props.data_load_function) {
        await props.data_load_function()
      }
      rows.value = props.data_get_function()
    }

    async function applyFilter() {
      let new_api_filter_string = ''
      // loop over all columns
      for (let column of m_columns.value) {
        // if non api field, skip
        if (column.non_api_field) {
          continue
        }
        // if filter string is not empty
        if (filter_strings_by_columns.value[column.field] !== '') {
          // if api_filter_string is not empty, add a &
          if (new_api_filter_string !== '') {
            new_api_filter_string += '&'
          }
          // add the filter string
          new_api_filter_string += '?' + column.field + '_contains=' + filter_strings_by_columns.value[column.field]
        }
      }
      // send the request if api_filter_string is not empty and if it changed
      if (new_api_filter_string !== '') {
        if (new_api_filter_string !== api_filter_string) {
          rows.value = await props.data_filter_function(new_api_filter_string)
          api_filter_string = new_api_filter_string
        }
      } else {
        await loadTableData()
      }
    }

    function showAll() {
      if (show_all.value) {
        m_visibleColumns.value = []
        for (let column of m_hideableColumns.value) {
          m_visibleColumns.value.push(column.field)
        }
        for (let column of m_nonHideableColumns.value) {
          m_visibleColumns.value.push(column.field)
        }
      }
      AdjustShowHideAll()
    }

    function hideAll() {
      if (hide_all.value) {
        m_visibleColumns.value = []
        for (let column of m_nonHideableColumns.value) {
          console.log(column.field)
          m_visibleColumns.value.push(column.field)
        }
      }
      AdjustShowHideAll()
    }

    function AdjustShowHideAll(){
      show_all.value = m_visibleColumns.value.length === m_columns.value.length;
      hide_all.value = m_visibleColumns.value.length === m_nonHideableColumns.value.length;
    }

    function DownloadFile(url: string, filename: string) {
      axios.get(url, {responseType: 'blob'}).then((response) => {
        exportFile(filename, response.data)
      })
    }

    return {
      rows,
      show_all,
      hide_all,
      showAll,
      hideAll,
      expand_column,
      AdjustShowHideAll,
      DownloadFile,
      m_columns,
      filter_row,
      m_visibleColumns,
      m_hideableColumns,
      filter_strings_by_columns,
      filter_strings_total,
      applyFilter,
    }
  }
}

</script>
