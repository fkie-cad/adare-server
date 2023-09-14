<template>
  <q-table
    :title="title"
    :rows="rows"
    :columns="COLUMNS"
    row-key="name"
    :visible-columns="visible_columns"
    class="tw-w-full"
    v-model:pagination="pagination"
    @request="OnRequest"
    :loading="loading"
  >
    <template v-slot:top="props">
      <div class="col">
        <div class="row">
          <q-btn
            flat dense
            :icon="props.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
            @click="props.toggleFullscreen"
          />

          <div class="col-3 q-ml-md">
            <div class="row q-table__title">{{ title }}</div>
          </div>
          <q-space />
          <q-input
            outlined
            dense
            v-model="search_filter"
            @update:model-value="ChangeSearchFilter()"
            label="search"
            style="width: 200px"
          >
            <template v-slot:append>
              <q-icon name="search" />
            </template>
          </q-input>
          <q-btn
            icon="filter_list"
            color="primary"
            class="q-mx-md"
            @click="show_filters = !show_filters"
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
                    v-model="show_all_columns"
                    label="show all"
                    @update:model-value="ShowAllColumns()"
                  />
                  <q-checkbox
                    v-model="hide_all_columns"
                    label="hide all"
                    @update:model-value="HideAllColumns()"
                  />
                </q-item>
                <q-separator />
                <q-item
                  v-for="col in hideable_columns"
                  :key="col.field"
                >
                  <q-checkbox v-model="visible_columns" :val=col.field :label="col.label" @update:model-value="AdjustShowHideAllColumns()"/>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
        <q-separator class="q-my-md" v-if="show_filters"/>
        <div class="row" v-if="show_filters">
        </div>
      </div>
    </template>
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
      <q-tr :props="props" v-if="show_filters">
        <q-td
          v-for="col in props.cols"
          :key="col.name"
          :props="props"
          style="border-bottom-width: 1px"
        >
          <q-input
            outlined
            dense
            v-model="column_filters[col.field]"
            @update:model-value="ChangeColumnFilter(col.field)"
            :label="'filter: '+col.label"
            :disable="col.disbale_filter"
            v-if="!col.hide_filter"
          />
        </q-td>
      </q-tr>
    </template>
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td
          v-for="col in props.cols"
          :key="col.field"
        >
          <div
            v-if="col.type=='user_icon'"
            class="tw-flex tw-items-center"
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
          <div v-else-if="col.type=='status'">
            <q-icon
              name="check_circle"
              color="positive"
              v-if="col.value.name == 'success'"
              size="32px"
            ><q-tooltip>success</q-tooltip></q-icon>
            <q-icon
              name="cancel"
              color="negative"
              v-if="col.value.name == 'failed'"
              size="32px"
            ><q-tooltip>failed</q-tooltip></q-icon>
          </div>
          <div v-else-if="col.type=='tags'" class="flex tw-flex-wrap tw-max-w-sm">
            <q-badge v-for="item in col.value" :key="item" color="primary" class="q-ma-xs">
              #{{ item }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='download'">
            <q-btn
              color="primary"
              icon="get_app"
              @click="DownloadFile(col.value, col.filename_function(col.value))"
              class="q-pa-sm q-ma-sm"
            >
              <q-tooltip>download</q-tooltip>
            </q-btn>
            <q-btn
              color="primary"
              icon="open_in_new"
              @click="ShowLog(props.row.uuid)"
              class="q-pa-sm q-ma-sm"
            >
              <q-tooltip>show log</q-tooltip>
            </q-btn>
          </div>
          <div v-else-if="col.type=='os_info'">
            <OsIcon :item="col.value.os"/> {{ col.value.distribution }}
          </div>
          <div v-else-if="col.type=='run_counts'">
            <q-badge color="positive" class="q-ma-sm">
              {{ col.value.successful }}
            </q-badge>
            <q-badge color="negative" class="q-ma-sm">
              {{ col.value.failed }}
            </q-badge>
          </div>
          <div v-else class="tw-max-w-md tw-break-all tw-inline-block tw-whitespace-break-spaces">
              {{ col.value }}
          </div>
        </q-td>
      </q-tr>
    </template>
    <template v-slot:loading>
      <q-inner-loading showing color="primary" />
    </template>
  </q-table>
</template>

<script lang="ts">
import {onMounted, ref} from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import {hideableColumnEntry, ColumnEntry, Filter, ColumnFilter, FilterToQueryString} from 'src/datatypes/advancedtable';
import axios from 'axios';
import API from 'src/api';
import {exportFile} from 'quasar';
import OsIcon from 'components/global/OsIcon.vue';
import { useRouter } from 'vue-router';

function extractFilenameFromUrl(url: string) {
  // dont use split
  // https://stackoverflow.com/questions/423376/how-to-get-the-file-name-from-a-full-path-using-javascript
  console.log(typeof url)
  console.log(url)
  return url.substring(url.lastIndexOf('/')+1);
}

// columns of table
const COLUMNS = [
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: true, hideable: true, type: 'status'},
  { name: 'uuid', label: 'uuid', field: 'uuid', align: 'left', sortable: true, hideable: true, },
  { name: 'publisher_name', align: 'left', label: 'publisher', field: 'publisher_name', hideable: true, type: 'user_icon'},
  { name: 'publish_date', align: 'left', label: 'publish date', field: 'publish_date', hideable: true},
  { name: 'timestamp_start', label: 'timestamp start', field: 'timestamp_start', align: 'left', sortable: true, hideable: true, },
  { name: 'timestamp_end', label: 'timestamp end', field: 'timestamp_end', align: 'left', sortable: true, hideable: true, },
  { name: 'logfile', label: 'logfile', field: 'logfile', align: 'left', hideable: true, type: 'download', filename_function: extractFilenameFromUrl}
]

// visible columns of table (when loading table for the first time)
const VISIBLE_COLUMNS = ['status', 'uuid', 'publisher_name', 'publish_date', 'timestamp_start', 'timestamp_end', 'logfile']


export default {
  name: 'ExperimentRunTable',
  components: {OsIcon, ProfileImage},

  props: {
    experiment: {
      type: String,
      required: false,
    },
  },

  setup(props) {
    // setup router
    const router = useRouter()

    // rows of table
    let rows = ref([])
    // columns of table
    let columns = ref<ColumnEntry[]>([])
    // visible columns of table
    let visible_columns = ref<string[]>([])
    // hideable columns of table
    let hideable_columns = ref<hideableColumnEntry[]>([])
    // non-hideable columns of table
    let non_hideable_columns = ref<ColumnEntry[]>([])

    // pagination state of table
    let pagination = ref({
      sortBy: 'desc',
      descending: false,
      page: 1,
      rowsPerPage: 8,
      rowsNumber: 10
    })

    // determines if all columns are shown/hidden
    let show_all_columns = ref(false)
    let hide_all_columns = ref(false)

    // determines if column filters as well as predefined filters are shown
    let show_filters = ref(false)

    // determines if a request is ongoing (to avoid too many requests when typing in search field/column filter field)
    let ongoing_request = false
    // determines if table is loading
    let loading = ref(false)

    // initialize column filters to be empty
    const column_filters = ref<ColumnFilter>({})
    // unchangable column filters (e.g. scenario)
    const unchangable_column_filters = ref<ColumnFilter>({})

    // initialize search filter to be empty
    let search_filter = ref('')

    // initialize filter object to contain no filter entries
    let FilterObject = ref<Filter>({
      'entries': []
    })

    // table title
    let table_title = ref('ExperimentRun Table')

    function SetUnchangableColumnFilter() {
      // apply unchangable column filters to column filters
      for (let column in unchangable_column_filters.value) {
        FilterObject.value.entries.push({
          'field': column,
          'type': 'eq',
          'value': unchangable_column_filters.value[column]
        })
      }
    }

    onMounted(async () => {
      // add experiment to unchangable column filters
      if (props.experiment) {
        unchangable_column_filters.value['experiment'] = props.experiment
        SetUnchangableColumnFilter()
      }

      columns.value = COLUMNS
      // setup hideable columns
      // get column field and label form props.columns
      for (let column of columns.value) {
        // add column to hideable columns if hideable property is set
        if (column.hideable) {
          hideable_columns.value.push(column)
        } else {
          non_hideable_columns.value.push(column)
        }
      }
      // set visible columns
      if (VISIBLE_COLUMNS) {
        visible_columns.value = VISIBLE_COLUMNS as string[]
      } else {
        // if no visible columns are set, set all columns to visible
        for (let column of columns.value) {
          visible_columns.value.push(column.field)
        }
      }
      // initialize column filters to be empty
      for (let column of columns.value) {
        column_filters.value[column.field] = ''
      }

      // load rows of table
      await ReloadTable()

      AdjustShowHideAllColumns()
    })

    // load rows of table from backend (with pagination, filtering and sorting)
    async function LoadTableData() {
      let offset = (pagination.value.page - 1) * pagination.value.rowsPerPage
      let limit = pagination.value.rowsPerPage
      let url = API.API+'experimentrun/?limit=' + limit + '&offset=' + offset
      // add filter to query string
      url += FilterToQueryString(FilterObject.value)
      // add sorting
      if (pagination.value.sortBy) {
        url += '&ordering=' + (pagination.value.descending ? '-' : '') + pagination.value.sortBy
      }
      let response = await axios.get(url)
      pagination.value.rowsNumber = response.data.count
      rows.value = response.data.results
    }

    // show all columns
    function ShowAllColumns() {
      if (show_all_columns.value) {
        visible_columns.value = []
        for (let column of hideable_columns.value) {
          visible_columns.value.push(column.field)
        }
        for (let column of non_hideable_columns.value) {
          visible_columns.value.push(column.field)
        }
      }
      AdjustShowHideAllColumns()
    }

    // hide all hideable columns
    function HideAllColumns() {
      if (hide_all_columns.value) {
        visible_columns.value = []
        for (let column of non_hideable_columns.value) {
          visible_columns.value.push(column.field)
        }
      }
      AdjustShowHideAllColumns()
    }

    // adjust show/hide all columns checkboxes to current state
    // all columns are shown -> show_all_columns is true
    // all columns are hidden -> hide_all_columns is true
    function AdjustShowHideAllColumns(){
      show_all_columns.value = visible_columns.value.length === columns.value.length;
      hide_all_columns.value = visible_columns.value.length === non_hideable_columns.value.length;
    }

    // used to update pagination and reload table data
    function OnRequest(props: any) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination
      loading.value = true
      // update pagination to current state
      pagination.value.page = page
      pagination.value.rowsPerPage = rowsPerPage
      pagination.value.sortBy = sortBy
      pagination.value.descending = descending

      LoadTableData()
      loading.value = false
    }

    // reload table data (and slow down requests to avoid too many requests)
    async function ReloadTable(delayed = false) {
      loading.value = true
      if (delayed){
        // slow down requests to avoid too many requests when typing in search field/column filter field
        if (!ongoing_request){
          ongoing_request = true
          setTimeout(async () => {
            await LoadTableData()
            ongoing_request = false
          }, 1000)
        }
      }else {
        await LoadTableData()
      }
      loading.value = false
    }


    // called when column filter is changed to update the table
    function ChangeColumnFilter(field: string){
      let contains_suffix = '_contains'
      let field_wsuffix = field + contains_suffix

      if (column_filters.value[field] === '') {
        // remove filter entry to the given field
        FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
          return !(entry.field === field_wsuffix && entry.type === 'search')
        })
      }else {
        // add new filter entry to the given field
        let exists = false
        for (let filter of FilterObject.value.entries) {
          if (filter.field === field_wsuffix && filter.type === 'search') {
            exists = true
            filter.value = column_filters.value[field]
          }
        }
        if (!exists) {
          FilterObject.value.entries.push({
            'field': field_wsuffix,
            'type': 'search',
            'value': column_filters.value[field]
          })
        }
      }
      ReloadTable(true)
    }

    // called when search filter is changed to update the table
    function ChangeSearchFilter(){
      if (search_filter.value === '') {
        // remove filter entry to the given field
        FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
          return !(entry.field === 'search' && entry.type === 'search')
        })
      } else {
        // add new filter entry to the given field
        let exists = false
        for (let filter of FilterObject.value.entries) {
          if (filter.field === 'search' && filter.type === 'search') {
            exists = true
            filter.value = search_filter.value
          }
        }
        if (!exists) {
          FilterObject.value.entries.push({
            'field': 'search',
            'type': 'search',
            'value': search_filter.value
          })
        }
      }
      ReloadTable(true)
    }

    // clear all filters and reload table
    function ClearFilters(){
      FilterObject.value.entries = []
      for (let column of columns.value) {
        column_filters.value[column.field] = ''
      }
      search_filter.value = ''
      SetUnchangableColumnFilter()
      ReloadTable()
    }

    function DownloadFile(url: string, filename: string) {
      const full_url = API.SERVER_URL + url
      axios.get(full_url, {responseType: 'blob'}).then((response) => {
        exportFile(filename, response.data)
      })
    }

    function ShowLog(experimentrun_uuid: string) {
      router.push({ path: `/logfile/${experimentrun_uuid}`})
    }

    return {
      title: table_title,
      rows,
      COLUMNS,
      visible_columns,
      columns,
      hideable_columns,
      pagination,
      show_all_columns,
      hide_all_columns,
      loading,
      show_filters,
      column_filters,
      search_filter,
      ShowAllColumns,
      HideAllColumns,
      AdjustShowHideAllColumns,
      OnRequest,
      ChangeColumnFilter,
      ClearFilters,
      ChangeSearchFilter,
      DownloadFile,
      ShowLog,
    }
  }
}

</script>
