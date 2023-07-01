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
          <q-list>
            <q-item
              v-for="col in m_hideableColumns"
              :key="col.field"
            >
              <q-toggle v-model="m_visibleColumns" :val=col.field :label="col.label"></q-toggle>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>

    </template>
    <template v-slot:body-cell="props">
      <td v-if="props.col.type=='user_icon'">
        <ProfileImage
          :username=props.value
          size="md"
          tooltip="true"
          linktoprofile="true"
          v-if="props.value"
        />
      </td>
      <td v-else-if="props.col.type=='forward'">
        <router-link :to="props.col.forward_url+props.row[props.col.forward_field]">
        <q-icon
          name="o_arrow_circle_right"
          size="40px"
        />
        </router-link>
      </td>
      <td v-else-if="props.col.type=='tags'">
        <q-badge v-for="item in props.value" :key="item" color="primary" class="q-ma-sm">
          {{ item }}
        </q-badge>
      </td>
      <td v-else-if="props.col.type=='run_counts'">
        <q-badge color="positive" class="q-ma-sm">
          {{ props.value.successful }}
        </q-badge>
        <q-badge color="negative" class="q-ma-sm">
          {{ props.value.failed }}
        </q-badge>
      </td>
      <td v-else>
        {{ props.value.toString() }}
      </td>
    </template>
  </q-table>
  </div>
</template>

<script lang="ts">
import {onMounted, ref} from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import {hideableColumnEntry, ColumnEntry} from 'src/datatypes/advancedtable';

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
      required: true,
    },
    title: {
      type: String,
      required: false,
      default: '',
    },
    data_load_function: {
      type: Function,
      required: true,
    },
    data_get_function: {
      type: Function,
      required: true,
    },
    data_filter_function: {
      type: Function,
      required: true,
    },
  },

  setup(props) {
    let rows = ref([])
    let m_columns = ref<ColumnEntry[]>([])
    let m_visibleColumns = ref<ColumnEntry[]>([])
    let m_hideableColumns = ref<hideableColumnEntry[]>([])
    let filter_row = ref(false);
    let api_filter_string = ''

    let filter_strings_by_columns: any = ref({})
    let filter_strings_total = ref('')

    onMounted(async () => {
      m_columns.value = props.columns
      // setup hideable columns
      // get column field and label form props.columns
      for (let column of m_columns.value) {
        // add column to hideable columns if hideable property is set
        if (column.hideable) {
          m_hideableColumns.value.push(column)
        }
      }
      // set visible columns
      m_visibleColumns.value = props.visibleColumns
      // setup filter strings
      filter_strings_by_columns.value = Object.keys(props.columns)
      // initialize all values to empty string
      for (let column of m_columns.value) {
        filter_strings_by_columns.value[column.field] = ''
      }
      // load rows of table
      await loadTableData()
    })

    async function loadTableData(){
      await props.data_load_function()
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

    return {
      rows,
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
