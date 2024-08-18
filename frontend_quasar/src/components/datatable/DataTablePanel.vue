<template>
  <div class="col">
    <div class="row tw-justify-between">
      <q-btn
        flat dense
        :icon="tableProps.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
        @click="tableProps.toggleFullscreen"
      />
      <div class="col-3 q-ml-md" v-if="title">
        <div class="row q-table__title">{{ title }}</div>
      </div>
      <q-space />
      <DataTableSearchFilter @update-searchFilter="updateFilter" class="q-mx-md"/>
      <q-btn
        icon="filter_list"
        color="primary"
        class="q-mx-md"
        @click="show_filters = !show_filters"
        v-if="filterEnabled && !no_filter"
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
        <DataTableSelectFilter
          v-for="filter in selectFilters"
          :key="filter.field"
          :filter="filter"
          :actualFilter="actualFilter"
          @update-selectFilter="updateFilter"
        />
<!--        <div class="q-pr-md">-->
<!--          <q-btn-dropdown-->
<!--              outline-->
<!--              icon="123"-->
<!--              label="run counts"-->
<!--              text-color="grey-8"-->
<!--              size="1.1em"-->
<!--            >-->
<!--              <div-->
<!--               v-for="filter in COUNT_FILTERS" v-bind:key="filter.field" class="q-pr-md"-->
<!--              >-->
<!--                <q-input-->
<!--                  dense-->
<!--                  outlined-->
<!--                  v-model="filter.value"-->
<!--                  :label="filter.name"-->
<!--                  class="tw-w-full q-pa-sm"-->
<!--                  @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"-->
<!--                  :rules="[ val => (Number(val) <= filter.max_value && Number(val) >= 0) || 'invalid input']"-->
<!--                />-->
<!--                <q-slider-->
<!--                  v-model="filter.value"-->
<!--                  :min="filter.min_value"-->
<!--                  :max="filter.max_value"-->
<!--                  :step="1"-->
<!--                  color="primary"-->
<!--                  class="q-px-md"-->
<!--                  :thumb-color="filter.color"-->
<!--                  :selection-color="filter.color"-->
<!--                  @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"-->
<!--                />-->
<!--              </div>-->
<!--            </q-btn-dropdown>-->
<!--        </div>-->
<!--        <div v-for="filter in DATE_FILTERS" v-bind:key="filter.field" class="q-pr-md">-->
<!--          <q-btn-dropdown-->
<!--              outline-->
<!--              icon="calendar_today"-->
<!--              :label="filter.name"-->
<!--              text-color="grey-8"-->
<!--              size="1.1em"-->
<!--          >-->
<!--            <div class="col">-->
<!--              <div class="row tw-bg-slate-100 justify-between">-->
<!--                <q-radio-->
<!--                  v-model="filter.toggle"-->
<!--                  :val="true"-->
<!--                  label="before"-->
<!--                  color="secondary"-->
<!--                  @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                />-->
<!--                <q-radio-->
<!--                  v-model="filter.toggle"-->
<!--                  :val="false"-->
<!--                  label="after"-->
<!--                  color="secondary"-->
<!--                  left-label-->
<!--                  @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                />-->
<!--              </div>-->
<!--              <div class="row tw-bg-slate-100">-->
<!--                <div class="q-gutter-sm">-->
<!--                  <q-radio v-model="filter.experimentrun_status" val="success" label="Success" color="positive" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                  <q-radio v-model="filter.experimentrun_status" val="all" label="All" color="secondary" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                  <q-radio v-model="filter.experimentrun_status" val="failed" label="Failed" color="negative" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                </div>-->
<!--              </div>-->
<!--              <q-date-->
<!--                v-model="filter.selected_date"-->
<!--                @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                class="row q-pa-sm"-->
<!--              />-->
<!--            </div>-->
<!--          </q-btn-dropdown>-->
<!--        </div>-->
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

<script lang="ts">
import { ref, onMounted } from 'vue';
import { CustomQTableColumn } from 'src/datatypes/quasar_extensions';
import { Filter, FilterEntry, FilterToQueryString } from 'src/datatypes/advancedtable';
import DataTableSearchFilter from 'components/datatable/DataTableSearchFilter.vue';
import DataTableSelectFilter from 'components/datatable/DataTableSelectFilter.vue';
import API from 'src/api';
import axios from 'axios';

export default {
  name: 'DataTablePanel',
  components: { DataTableSelectFilter, DataTableSearchFilter },
  props: {
    tableProps: {
      type: Object,
      required: true,
    },
    visibleColumns: {
      type: Array as () => string[],
      required: true,
    },
    columns: {
      type: Array,
      required: true,
    },
    filterEnabled: {
      type: Boolean,
      default: true,
    },
    selectFilters: {
      type: Array,
      default: () => [],
    },
    api: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      default: '',
    }
  },
  emits: ['update-visibleColumns', 'update-filter'],

  setup(props, {emit}) {

    const show_all_columns = ref(false);
    const hide_all_columns = ref(false);
    const visible_columns = ref<string[]>(props.visibleColumns);
    const hideable_columns = ref<CustomQTableColumn[]>([]);
    const show_filters = ref(false);
    const no_filter = ref(false);

    let actualFilter = ref<Filter>({
      'entries': []
    })

    function updateFilter(filter: FilterEntry) {
      actualFilter.value.entries = actualFilter.value.entries.filter((entry: FilterEntry) => entry.field !== filter.field);
      actualFilter.value.entries.push(filter);
      // console.log('filterObject', actualFilter.value);
      emit('update-filter', actualFilter.value);
    }

    async function LoadFilterOptions(){
      let url = props.api+'/filteroptions/?'+FilterToQueryString(actualFilter.value)
      let response = await axios.get(url)
      // set options of predefined filters
      for (let filter of props.selectFilters) {
        filter.options = response.data[filter.option_api_field]
        filter.total_options = response.data[filter.option_api_field]
      }
    }

    // add on mounted to adjust show/hide all columns
    onMounted(() => {
      // check if visibleColumns is empty, if so, set hide_all_columns to true
      if (props.visibleColumns.length === 0) {
        hide_all_columns.value = true;
      }
      // check if visibleColumns is full, if so, set show_all_columns to true
      if (props.visibleColumns.length === props.columns.length) {
        show_all_columns.value = true;
      }

      // set hideable columns to all columns where column.hideable is true
      hideable_columns.value = props.columns.filter((col: CustomQTableColumn) => col.hideable);

      // load filter options
      LoadFilterOptions()

      if (props.selectFilters.length == 0) {
        no_filter.value = true;
      }

    });

    function ShowAllColumns() {
      show_all_columns.value = true;
      hide_all_columns.value = false;
      visible_columns.value = props.columns.map((col: CustomQTableColumn) => col.field);
      emit('update-visibleColumns', visible_columns.value);
    }

    function HideAllColumns() {
      hide_all_columns.value = true;
      show_all_columns.value = false;
      visible_columns.value = props.columns.filter((col: CustomQTableColumn) => !col.hideable).map((col: CustomQTableColumn) => col.field);
      emit('update-visibleColumns', visible_columns.value);
    }

    function AdjustShowHideAllColumns(){
      // adjust the show_all_columns and hide_all_columns based on visible_columns
      // if all columns are visible, set show_all_columns to true
      // if no columns are visible, set hide_all_columns to true
      // if some columns are visible, set both to false
      // make sure to always show all non hideable columns
      if (visible_columns.value.length === props.columns.length) {
        show_all_columns.value = true;
        hide_all_columns.value = false;
      } else if (visible_columns.value.length === (props.columns.length - hideable_columns.value.length)) {
        hide_all_columns.value = true;
        show_all_columns.value = false;
      } else {
        hide_all_columns.value = false;
        show_all_columns.value = false;
      }
      emit('update-visibleColumns', visible_columns.value);
    }

    return {
      show_all_columns,
      hide_all_columns,
      visible_columns,
      hideable_columns,
      show_filters,
      actualFilter,
      no_filter,
      AdjustShowHideAllColumns,
      ShowAllColumns,
      HideAllColumns,
      updateFilter,
    };
  },
};
</script>
