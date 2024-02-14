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
            <div class="row q-table__subtitle" v-if="scenario">(Scenario {{ scenario }})</div>
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
            <div class="q-pr-md">
              <q-btn-dropdown
                  outline
                  icon="123"
                  label="run counts"
                  text-color="grey-8"
                  size="1.1em"
                >
                  <div
                   v-for="filter in COUNT_FILTERS" v-bind:key="filter.field" class="q-pr-md"
                  >
                    <q-input
                      dense
                      outlined
                      v-model="filter.value"
                      :label="filter.name"
                      class="tw-w-full q-pa-sm"
                      @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"
                      :rules="[ val => (Number(val) <= filter.max_value && Number(val) >= 0) || 'invalid input']"
                    />
                    <q-slider
                      v-model="filter.value"
                      :min="filter.min_value"
                      :max="filter.max_value"
                      :step="1"
                      color="primary"
                      class="q-px-md"
                      :thumb-color="filter.color"
                      :selection-color="filter.color"
                      @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"
                    />
                  </div>
                </q-btn-dropdown>
            </div>
            <div v-for="filter in DATE_FILTERS" v-bind:key="filter.field" class="q-pr-md">
              <q-btn-dropdown
                  outline
                  icon="calendar_today"
                  :label="filter.name"
                  text-color="grey-8"
                  size="1.1em"
              >
                <div class="col">
                  <div class="row tw-bg-slate-100 justify-between">
                    <q-radio
                      v-model="filter.toggle"
                      :val="true"
                      label="before"
                      color="secondary"
                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"
                    />
                    <q-radio
                      v-model="filter.toggle"
                      :val="false"
                      label="after"
                      color="secondary"
                      left-label
                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"
                    />
<!--                    <q-toggle-->
<!--                      :label="filter.toggle?'before the date':'after the date'"-->
<!--                      color="primary"-->
<!--                      v-model="filter.toggle"-->
<!--                      class="q-pa-sm"-->
<!--                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                    />-->

                  </div>
                  <div class="row tw-bg-slate-100">
                    <div class="q-gutter-sm">
                      <q-radio v-model="filter.experimentrun_status" val="success" label="Success" color="positive" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>
                      <q-radio v-model="filter.experimentrun_status" val="all" label="All" color="secondary" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>
                      <q-radio v-model="filter.experimentrun_status" val="failed" label="Failed" color="negative" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>
                    </div>
                  </div>
                  <q-date
                    v-model="filter.selected_date"
                    @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"
                    class="row q-pa-sm"
                  />
                </div>
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
              :avatar="col.value.avatar"
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
          <div v-else-if="col.type=='tags'" class="flex tw-flex-wrap tw-max-w-sm">
            <q-badge v-for="item in col.value" :key="item" color="primary" class="q-ma-xs">
              #{{ item }}
            </q-badge>
          </div>
          <div v-else-if="col.type=='download'">
            <q-btn
              color="primary"
              icon="get_app"
              @click="DownloadFile(col.value, col.filename_function(props.row))"
              class="q-px-sm q-mx-sm"
            >
              <q-tooltip>download</q-tooltip>
            </q-btn>
          </div>
          <div v-else-if="col.type=='external_link'">
            <q-btn
              color="primary"
              icon="get_app"
              @click="OpenInNewTab(col.value)"
              class="q-px-sm q-mx-sm"
            >
              <q-tooltip>go to gitea</q-tooltip>
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

// columns of table
const COLUMNS = [
  { name: 'details', label: 'details', field: 'details', align: 'left', hideable: true, non_api_field: true, type: 'link', link_field: 'uuid', link_url: '/experimentdetails/', link_icon: 'o_add_circle', hide_filter: true},
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true},
  { name: 'os_info', label: 'os', field: 'os_info', align: 'left', sortable: true, hideable: true, type: 'os_info'},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true},
  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true},
  { name: 'published_by', align: 'left', label: 'publisher', field: 'published_by', hideable: true, type: 'user_icon'},
  { name: 'published_at', align: 'left', label: 'publish date', field: 'published_at', hideable: true},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, type: 'tags'},
  { name: 'run_counts', align: 'left', label: 'run counts', field: 'run_counts', hideable: true, type:'run_counts', hide_filter: true},
  { name: 'action_file', align: 'left', label: 'action file', field: 'action_file', hideable: true, type:'external_link',},
  { name: 'testset_file', align: 'left', label: 'testset file', field: 'testset_file', hideable: true, type:'external_link',},
  { name: 'metadata_file', align: 'left', label: 'metadata file', field: 'metadata_file', hideable: true, type:'external_link',},
]

// visible columns of table (when loading table for the first time)
const VISIBLE_COLUMNS = ['details', 'name', 'os', 'description', 'published_by', 'tags', 'run_counts', 'action_file', 'testset_file', 'metadata_file']

// predefined selection filters of table
const SELECT_FILTERS = ref([
  { name: 'tags', field: 'tags', api_field: 'tags_mc', option_api_field: 'tags', type: 'options_mc', options: [] as string[], total_options: [] as string[], selected: []},
])

// predefined count filters of table
const COUNT_FILTERS = ref([
  { name: 'success', color: 'positive', field: 'min_runs_success', api_field: 'min_runcount_pos', max_api_field: 'max_success', min_value: 0, max_value: 0, value: 0},
  { name: 'failed', color: 'negative', field: 'min_runs_failed', api_field: 'min_runcount_neg', max_api_field: 'max_failed', min_value: 0, max_value: 0, value: 0},
  { name: 'all', color: 'info', field: 'min_runs_total', api_field: 'min_runcount', max_api_field: 'total_count', min_value: 0, max_value: 0, value: 0},
])

const DATE_FILTERS = ref([
  { name: 'latest experiment run', field: 'latest_experiment_run', api_field: 'latest_experiment_run', selected_date: '', toggle: false, experimentrun_status: 'all'}
])


export default {
  name: 'ExperimentTable',
  components: {OsIcon, ProfileImage},

  props: {
    scenario: {
      type: String,
      required: false,
    },
  },

  setup(props) {
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
    let table_title = ref('Experiment Table')


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

    function OpenInNewTab(url: string){
      window.open(url, '_blank')
    }


    onMounted(async () => {

      // add scenario to unchangable column filters and remove column for scenario
      if (props.scenario) {
        unchangable_column_filters.value['scenario_eq'] = props.scenario
        columns.value = columns.value.filter(column => column.field != 'scenario')
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
      let url = API.API+'experiment/?limit=' + limit + '&offset=' + offset
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
      let url = API.API+'experiment/filteroptions/?'+FilterToQueryString(FilterObject.value)
      let response = await axios.get(url)
      // set options of predefined filters
      for (let filter of SELECT_FILTERS.value) {
        filter.options = response.data[filter.option_api_field]
        filter.total_options = response.data[filter.option_api_field]
      }
      // set run count max values
      for (let filter of COUNT_FILTERS.value) {
        filter.max_value = response.data[filter.max_api_field]
      }
    }

    async function ChangeCountFilter(api_field: string, value: number){
      // remove filter entry if exists
      for (let filter of FilterObject.value.entries) {
        if (filter.field === api_field && filter.type === 'count') {
          FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
            return !(entry.field === api_field && entry.type === 'count')
          })
        }
      }
      // change min value for all run count filter to sum of the other run count filters
      let sum = 0
      for (let filter of COUNT_FILTERS.value) {
        if (filter.field !== 'min_runs_total') {
          sum += filter.value
        }
      }
      // get count filter with field 'min_runs_total'
      let total_count_filter = COUNT_FILTERS.value.filter((filter) => {
        return filter.field === 'min_runs_total'
      })
      total_count_filter[0].min_value = sum
      if (total_count_filter[0].value < sum) {
        total_count_filter[0].value = sum
      }

      // add new filter entry to the given api field
      if (value > 0){
        FilterObject.value.entries.push({
          'field': api_field,
          'type': 'count',
          'value': value.toString()
        })
      }
      await ReloadTable()
    }

    async function ChangeDateFilter(api_field: string, value: string, before: boolean, experimentrun_status: string){
      // cast value to date string for django
      value = new Date(value).toISOString().slice(0, 10)
      // remove filter entry if exists
      for (let filter of FilterObject.value.entries) {
        if (filter.field.includes(api_field) && filter.type === 'date') {
          FilterObject.value.entries = FilterObject.value.entries.filter((entry) => {
            return !(entry.field.includes(api_field) && entry.type === 'date')
          })
        }
      }

      // add new filter entry to the given api field
      FilterObject.value.entries.push({
        'field': api_field+'_'+(before? 'before' : 'after'),
        'type': 'date',
        'value': value.toString()+','+experimentrun_status
      })

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
      for (let filter of COUNT_FILTERS.value) {
        filter.max_value = 0
      }
      for (let filter of DATE_FILTERS.value) {
        filter.selected_date = ''
        filter.toggle = false
        filter.experimentrun_status = 'all'
      }
      for (let column of columns.value) {
        column_filters.value[column.field] = ''
      }
      search_filter.value = ''
      SetUnchangableColumnFilter()
      ReloadTable()
    }

    function DownloadFile(url: string, filename: string) {
      axios.get(url, {responseType: 'blob'}).then((response) => {
        exportFile(filename, response.data)
      })
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
      SELECT_FILTERS,
      COUNT_FILTERS,
      DATE_FILTERS,
      column_filters,
      search_filter,
      ShowAllColumns,
      HideAllColumns,
      AdjustShowHideAllColumns,
      OnRequest,
      ChangeSelectFilter,
      ChangeCountFilter,
      ChangeDateFilter,
      FilterSelect,
      ChangeColumnFilter,
      ClearFilters,
      ChangeSearchFilter,
      DownloadFile,
      OpenInNewTab
    }
  }
}

</script>
