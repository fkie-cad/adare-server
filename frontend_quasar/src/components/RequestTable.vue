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
            flat round dense
            :icon="props.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
            @click="props.toggleFullscreen"
          />

          <div class="col-2 q-table__title q-ml-md">{{ title }}</div>
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
        <q-separator class="q-my-md" v-if="show_filters & PREDEFINED_FILTERS.length > 0"/>
        <div class="row" v-if="show_filters & PREDEFINED_FILTERS.length > 0">
          <div class="col flex justify-start">
            <div v-for="filter in PREDEFINED_FILTERS" v-bind:key="filter.field" class="q-pr-md">
              <q-select
                outlined
                dense
                options-dense
                use-input
                input-debounce="0"
                v-model="filter.selected"
                :label="filter.name"
                :options="filter.options"
                :multiple="filter.type=='options_mc'"
                display-value=""
                @update:model-value="ChangeFilterEntry(filter.api_field)"
                @clear="ChangeFilterEntry(filter.api_field)"
                style="width: 200px"
                @filter="(val, update, abort) => { FilterSelect(val, update, abort, filter.field) }"
              >
                <template v-slot:option="scope">
                  <q-item v-bind="scope.itemProps">
                    <q-item-section>
                      <q-item-label>
                        <q-icon name="check" v-if="scope.selected" size="1rem"/>
                        <q-icon v-else size="1rem"/>
                        {{ scope.opt }}
                      </q-item-label>
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>
            </div>
          </div>
          <div class="col-auto">
            <q-btn
              label="clear filters"
              icon="clear"
              rounded
              @click="ClearFilters()"
            />
          </div>
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
          <div v-else-if="col.type=='status_icon'">
            <StatusIcon :status="col.value.name" />
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
          <div
            v-else-if="col.type=='category'"
            >
            <RequestItemIcon
              :item="col.value"
            />
          </div>
          <div v-else-if="col.type=='details'">
            <q-icon
              name="add_circle"
              size="2.5em"
              color="secondary"
              @click="NavigateToDetails(props.row.uuid)"
            />
          </div>
          <div v-else-if="col.type=='tags'" class="flex tw-flex-wrap tw-max-w-sm">
            <q-badge v-for="item in col.value" :key="item" color="primary" class="q-ma-xs">
              #{{ item }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='labels'" class="flex tw-flex-wrap tw-max-w-sm">
            <q-badge v-for="item in col.value" :key="item" color="primary" class="q-ma-xs">
              {{ item }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='testfunction'">
            {{ col.value.name }}
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
import { useRouter } from 'vue-router';
import RequestItemIcon from 'components/global/RequestItemIcon.vue';
import StatusIcon from 'components/global/StatusIcon.vue';

// columns of table
const COLUMNS = [
  { name: 'details', align: 'left', label: 'details', field: 'details', hideable: false, type: 'details', hide_filter: true},
  { name: 'title', align: 'left', label: 'title', field: 'title', hideable: false},
  { name: 'status', align: 'left', label: 'status', field: 'status', hideable: true, type: 'status_icon', hide_filter: true},
  { name: 'category_type', align: 'left', label: 'category', field: 'category_type', hideable: true, type: 'category', hide_filter: true,},
  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true},
  { name: 'last_changed', align: 'left', label: 'last changed', field: 'last_changed', hideable: true},
  { name: 'requestor', align: 'left', label: 'requestor', field: 'requestor', hideable: true, type: 'user_icon'},
  { name: 'request_creation_date', align: 'left', label: 'creation data', field: 'request_creation_date', hideable: true},
  { name: 'supervisor', align: 'left', label: 'supervisor', field: 'supervisor', hideable: true, type: 'user_icon'},
  { name: 'supervisor_assigned_by', align: 'left', label: 'assigned by', field: 'supervisor_assigned_by', hideable: true, type: 'user_icon'},
  { name: 'labels', align: 'left', label: 'labels', field: 'labels', type:'labels', hideable: true},
]


// visible columns of table (when loading table for the first time)
const VISIBLE_COLUMNS =  [
  'details',
  'status',
  'category_type',
  'description',
  'last_changed',
  'requestor',
  'supervisor',
]

// predefined filters of table
const PREDEFINED_FILTERS = ref([
  { name: 'status', field: 'status', api_field: 'status_mc', type: 'options_mc', options: [] as string[], total_options: [] as string[], selected: []},
  { name: 'category', field: 'category', api_field: 'category_mc', type: 'options_mc', options: [] as string[], total_options: [] as string[], selected: []},
])


export default {
  name: 'RequestTable',
  components: {StatusIcon, RequestItemIcon, ProfileImage},

  setup(props) {
    // load router
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
    // initialize search filter to be empty
    let search_filter = ref('')

    // initialize filter object to contain no filter entries
    let FilterObject = ref<Filter>({
      'entries': []
    })


    onMounted(async () => {
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
      // load predefined filter options
      await LoadFilterOptions()

      AdjustShowHideAllColumns()
    })

    // load rows of table from backend (with pagination, filtering and sorting)
    async function LoadTableData() {
      let offset = (pagination.value.page - 1) * pagination.value.rowsPerPage
      let limit = pagination.value.rowsPerPage
      let url = API.API+'request/?limit=' + limit + '&offset=' + offset
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

    // load filter options for all predefined filters
    async function LoadFilterOptions(){
      for (let filter of PREDEFINED_FILTERS.value) {
        let url = API.API+'request/filteroptions/' + filter.field + '/'
        let response = await axios.get(url)
        filter.options = response.data
        filter.total_options = response.data
      }
    }

    // called when predefined filter is changed to update the table
    async function ChangeFilterEntry(field: string){
      // get values of filter select stored in predefined_filters as an array
      let values: string[] = []
      for (let filter of PREDEFINED_FILTERS.value) {
        if (filter.api_field === field) {
          values = filter.selected
        }
      }
      // remove filter entry to the given field
      for (let filter of FilterObject.value.entries) {
        if (filter.field === field && filter.type === 'select') {
          if (!values) {
            FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
              return !(entry.field === field && entry.type === 'select')
            })
          } else if (!values.includes(filter.value)) {
            FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
              return !(entry.field === field && entry.type === 'select' && entry.value === filter.value)
            })
          }
        }
      }
      // add new filter entry to the given field
      if (values){
        values.forEach((val) => {
          // check if filter entry already exists
          let exists = false
          for (let filter of FilterObject.value.entries) {
            if (filter.field === field && filter.type === 'select' && filter.value === val) {
              exists = true
            }
          }
          if (!exists) {
            FilterObject.value.entries.push({
              'field': field,
              'type': 'select',
              'value': val
            })
          }
        })
      }
      await ReloadTable()
    }

    // function used in the quasar select element to update the options of the select element
    function FilterSelect(val: string, update: (arg0: { (): void; (): void; }) => void, abort: never, field: string) {
      // get options of filter select stored in predefined_filters
      let options: string[] = []
      let index = 0
      for (let filter of PREDEFINED_FILTERS.value) {
        if (filter.field === field) {
          options = filter.total_options
          index = PREDEFINED_FILTERS.value.indexOf(filter)
        }
      }
      if (val === '') {
        // reset options of filter select
        update(() => {
          PREDEFINED_FILTERS.value[index].options = options
        })
        return
      }
      // filter options
      let filtered_options = options.filter((option) => {
        return option.toLowerCase().includes(val.toLowerCase())
      })
      // update options of filter select
      update(() => {
        // update options of filter select
        PREDEFINED_FILTERS.value[index].options = filtered_options
      })
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
      for (let filter of PREDEFINED_FILTERS.value) {
        filter.selected = []
      }
      for (let column of columns.value) {
        column_filters.value[column.field] = ''
      }
      search_filter.value = ''
      ReloadTable()
    }

    function NavigateToDetails(request_uuid: string){
      router.push({'path': '/requests/' + request_uuid})
    }

    return {
      title: 'Request Table',
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
      PREDEFINED_FILTERS,
      column_filters,
      search_filter,
      ShowAllColumns,
      HideAllColumns,
      AdjustShowHideAllColumns,
      OnRequest,
      ChangeFilterEntry,
      FilterSelect,
      ChangeColumnFilter,
      ClearFilters,
      ChangeSearchFilter,
      NavigateToDetails,
    }
  }
}

</script>
