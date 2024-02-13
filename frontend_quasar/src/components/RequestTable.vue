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

          <div class="col-2 q-table__title q-ml-md">{{ title }}</div>
          <q-space />
          <q-btn-group
            push
            class="q-mx-md"
          >
            <q-btn push label="Show my" @click="ToggleUserFilter" :color="user_toggle_filter_active? 'primary':'blue-grey-1'" :text-color="user_toggle_filter_active? 'white':'black'"/>
            <q-btn push label="Show all" @click="ToggleUserFilter" :color="user_toggle_filter_active? 'blue-grey-1':'primary'" :text-color="user_toggle_filter_active? 'black':'white'"/>
          </q-btn-group>
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
          <div class="col flex justify-start">
            <div v-for="filter in SELECT_FILTERS" v-bind:key="filter.field" class="q-pr-md">
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
                @update:model-value="ChangeSelectFilter(filter.api_field)"
                @clear="ChangeSelectFilter(filter.api_field)"
                style="width: 200px"
                @filter="(val, update, abort) => { FilterSelect(val, update, abort, filter.field) }"
                v-if="filter.type=='options_mc'"
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
            <div v-for="filter in DATERANGE_FILTERS" v-bind:key="filter.field" class="q-pr-md">
              <q-btn-dropdown
                  outline
                  icon="calendar_today"
                  :label="filter.name"
                  text-color="grey-8"
                  size="1.1em"
              >
                <q-date
                    v-model="filter.selected_daterange"
                    range
                    @update:model-value="ChangeDateRangeFilter(filter.api_field, filter.selected_daterange)"
                />
              </q-btn-dropdown>
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
              :username=col.value.username
              size="md"
              :tooltip=true
              :linktoprofile=true
              :avatar_url=col.value.avatar
              v-if=col.value
            />
          </div>
          <div
            v-else-if="col.type=='gitea_link'"
            class="tw-flex tw-items-center"
          >
            <q-icon
              name="link"
              size="32px"
              color="secondary"
              @click="OpenInNewTab(col.value)"
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
            <q-badge v-for="item in col.value" :key="item" class="q-ma-xs" :style="{color: item.color}">
              {{ item.name }}
              <q-tooltip v-if="item.description">
                <div>{{ item.description }}</div>
              </q-tooltip>
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
import { useLoggedInUserStore } from 'src/stores/loggedinuser';
import { useLoginStore } from 'src/stores/login';

// columns of table
const COLUMNS = [
  { name: 'details', align: 'left', label: 'details', field: 'details', hideable: false, type: 'details', hide_filter: true},
  { name: 'title', align: 'left', label: 'title', field: 'title', hideable: false},
  { name: 'action', align: 'left', label: 'action', field: 'action', hideable: true},
  { name: 'objective_name', align: 'left', label: 'objective', field: 'objective_name', hideable: true},

  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true},
  { name: 'last_change_date', align: 'left', label: 'last changed', field: 'last_change_date', hideable: true},
  { name: 'creation_date', align: 'left', label: 'creation date', field: 'creation_date', hideable: true},
  { name: 'labels', align: 'left', label: 'labels', field: 'labels', type:'labels', hideable: true},
  { name: 'gitea_pr_url', align: 'left', label: 'pull request link', field: 'gitea_pr_url', type:'gitea_link', hideable: true},
  { name: 'requester', align: 'left', label: 'requester', field: 'requester', hideable: true, type: 'user_icon'},

  // { name: 'status', align: 'left', label: 'status', field: 'status', hideable: true, type: 'status_icon', hide_filter: true},
  // { name: 'category_type', align: 'left', label: 'category', field: 'category_type', hideable: true, type: 'category', hide_filter: true,},
  // { name: 'last_changed', align: 'left', label: 'last changed', field: 'last_changed', hideable: true},
  // { name: 'requestor', align: 'left', label: 'requestor', field: 'requestor', hideable: true, type: 'user_icon'},
  // { name: 'request_creation_date', align: 'left', label: 'creation data', field: 'request_creation_date', hideable: true},
  // { name: 'supervisor', align: 'left', label: 'supervisor', field: 'supervisor', hideable: true, type: 'user_icon'},
  // { name: 'supervisor_assigned_by', align: 'left', label: 'assigned by', field: 'supervisor_assigned_by', hideable: true, type: 'user_icon'},
]


// visible columns of table (when loading table for the first time)
const VISIBLE_COLUMNS =  [
  'details',
  'action',
  'objective_name',
  'requester',
  'gitea_pr_url',
]

// predefined filters of table
const SELECT_FILTERS = ref([
  { name: 'status', field: 'status', api_field: 'status_mc', type: 'options_mc', option_api_field: 'status', options: [] as string[], total_options: [] as string[], selected: []},
  { name: 'category', field: 'category', api_field: 'category_mc', type: 'options_mc', option_api_field: 'category', options: [] as string[], total_options: [] as string[], selected: []},
])

const DATERANGE_FILTERS = ref([
  { name: 'last changed', field: 'last_changed', api_field: 'last_changed', type: 'date_range', selected_daterange: null},
])




export default {
  name: 'RequestTable',
  components: {StatusIcon, RequestItemIcon, ProfileImage},

  setup(props) {
    // load router
    const router = useRouter()

    //
    const LoggedInUserStore = useLoggedInUserStore()

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

    //
    let show_date_filter = ref(false)



    // determines if column filters as well as predefined filters are shown
    let show_filters = ref(false)

    // determines if a request is ongoing (to avoid too many requests when typing in search field/column filter field)
    let ongoing_request = false
    // determines if table is loading
    let loading = ref(false)

    // initialize column filters to be empty
    const column_filters = ref<ColumnFilter>({})

    let user_toggle_filter_active = ref(false)

    // initialize search filter to be empty
    let search_filter = ref('')

    // initialize filter object to contain no filter entries
    let FilterObject = ref<Filter>({
      'entries': []
    })

    async function ToggleUserFilter() {
      loading.value = true
      if (user_toggle_filter_active.value){
        // remove user filter
        FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
          return entry.field != 'username'
        })
      } else {
        // add user filter
        FilterObject.value.entries.push({
          'field': 'username',
          'type': '',
          'value': LoggedInUserStore.username
        })
      }
      user_toggle_filter_active.value = !user_toggle_filter_active.value
      await ReloadTable(true)
      loading.value = false
    }

    function SetupUserFilter(){
      if (user_toggle_filter_active.value){
        // add user filter
        FilterObject.value.entries.push({
          'field': 'username',
          'type': '',
          'value': LoggedInUserStore.username
        })
      }
    }

    onMounted(async () => {
      SetupUserFilter()
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
      loading.value = true
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
      console.log(response.data)
      pagination.value.rowsNumber = response.data.count
      rows.value = response.data.results
      loading.value = false
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
            await LoadFilterOptions()
            ongoing_request = false
          }, 1000)
        }
      }else {
        await LoadTableData()
        await LoadFilterOptions()
      }
      loading.value = false
    }


    // load filter options for all predefined filters
    async function LoadFilterOptions(){
      let url = API.API+'request/filteroptions/?'+FilterToQueryString(FilterObject.value)
      let response = await axios.get(url)
      // set options of predefined filters
      for (let filter of SELECT_FILTERS.value) {
        filter.options = response.data[filter.option_api_field]
        filter.total_options = response.data[filter.option_api_field]
      }
    }

    // function used in the quasar select element to update the options of the select element
    function FilterSelect(val: string, update: (arg0: { (): void; (): void; }) => void, abort: never, field: string) {
      // get options of filter select stored in predefined_filters
      let options: string[] = []
      let index = 0
      for (let filter of SELECT_FILTERS.value) {
        if (filter.field === field) {
          options = filter.total_options
          index = SELECT_FILTERS.value.indexOf(filter)
        }
      }
      if (val === '') {
        // reset options of filter select
        update(() => {
          SELECT_FILTERS.value[index].options = options
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
        SELECT_FILTERS.value[index].options = filtered_options
      })
    }

    async function ChangeDateRangeFilter(api_field: string, value: { from: string; to: string } | string){
      // cast value to date string for django
      let from_date = ''
      let to_date = ''
      if (value !== null) {
        if (typeof value === 'string') {
          from_date = new Date(value).toISOString().slice(0, 10)
          to_date = new Date(value).toISOString().slice(0, 10)
        } else {
          from_date = new Date(value.from).toISOString().slice(0, 10)
          to_date = new Date(value.to).toISOString().slice(0, 10)
        }
      }
      // remove filter entry if exists (pay attention that api_field is used with suffix _from and _to)
      for (let filter of FilterObject.value.entries) {
        if (filter.type === 'daterange') {
          FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
            return !(entry.field === (api_field+'_from') && entry.type === 'daterange')
          })
          FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
            return !(entry.field === (api_field+'_to') && entry.type === 'daterange')
          })
        }
      }

      if (value !== null) {
        // add new filter entry to the given api field
        FilterObject.value.entries.push({
          'field': api_field+'_from',
          'type': 'daterange',
          'value': from_date
        })
        FilterObject.value.entries.push({
          'field': api_field+'_to',
          'type': 'daterange',
          'value': to_date
        })
      }

      await ReloadTable()
    }

    // called when predefined filter is changed to update the table
    async function ChangeSelectFilter(field: string){
      // get values of filter select stored in predefined_filters as an array
      let values: string[] = []
      for (let filter of SELECT_FILTERS.value) {
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
      for (let filter of SELECT_FILTERS.value) {
        filter.selected = []
      }
      for (let filter of DATERANGE_FILTERS.value) {
        filter.selected_daterange = null
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

    function OpenInNewTab(url: string){
      window.open(url, '_blank')
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
      SELECT_FILTERS,
      DATERANGE_FILTERS,
      column_filters,
      search_filter,
      user_toggle_filter_active,
      show_date_filter,
      ShowAllColumns,
      HideAllColumns,
      AdjustShowHideAllColumns,
      OnRequest,
      ChangeDateRangeFilter,
      ChangeSelectFilter,
      FilterSelect,
      ChangeColumnFilter,
      ClearFilters,
      ChangeSearchFilter,
      NavigateToDetails,
      ToggleUserFilter,
      OpenInNewTab,
    }
  }
}

</script>
