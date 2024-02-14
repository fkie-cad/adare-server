<template>
  <q-table
    :title="title"
    :rows="rows"
    :columns="columns"
    row-key="name"
    :visible-columns="visibleColumns"
    class="tw-w-full"
    v-model:pagination="mutablePagination"
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
<!--        <div class="row" v-if="show_filters">-->
<!--          <div class="col flex justify-start">-->
<!--            <div v-for="filter in SELECT_FILTERS" v-bind:key="filter.field" class="q-pr-md">-->
<!--              <q-select-->
<!--                outlined-->
<!--                dense-->
<!--                options-dense-->
<!--                use-input-->
<!--                input-debounce="0"-->
<!--                v-model="filter.selected"-->
<!--                :label="filter.name"-->
<!--                :options="filter.options"-->
<!--                :multiple="filter.type=='options_mc'"-->
<!--                display-value=""-->
<!--                @update:model-value="ChangeSelectFilter(filter.api_field)"-->
<!--                @clear="ChangeSelectFilter(filter.api_field)"-->
<!--                style="width: 200px"-->
<!--                @filter="(val, update, abort) => { FilterSelect(val, update, abort, filter.field) }"-->
<!--                v-if="filter.type=='options_mc'"-->
<!--              >-->
<!--                <template v-slot:option="scope">-->
<!--                  <q-item v-bind="scope.itemProps">-->
<!--                    <q-item-section>-->
<!--                      <q-item-label>-->
<!--                        <q-icon name="check" v-if="scope.selected" size="1rem"/>-->
<!--                        <q-icon v-else size="1rem"/>-->
<!--                        {{ scope.opt }}-->
<!--                      </q-item-label>-->
<!--                    </q-item-section>-->
<!--                  </q-item>-->
<!--                </template>-->
<!--              </q-select>-->
<!--            </div>-->
<!--            <div class="q-pr-md">-->
<!--              <q-btn-dropdown-->
<!--                  outline-->
<!--                  icon="123"-->
<!--                  label="run counts"-->
<!--                  text-color="grey-8"-->
<!--                  size="1.1em"-->
<!--                >-->
<!--                  <div-->
<!--                   v-for="filter in COUNT_FILTERS" v-bind:key="filter.field" class="q-pr-md"-->
<!--                  >-->
<!--                    <q-input-->
<!--                      dense-->
<!--                      outlined-->
<!--                      v-model="filter.value"-->
<!--                      :label="filter.name"-->
<!--                      class="tw-w-full q-pa-sm"-->
<!--                      @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"-->
<!--                      :rules="[ val => (Number(val) <= filter.max_value && Number(val) >= 0) || 'invalid input']"-->
<!--                    />-->
<!--                    <q-slider-->
<!--                      v-model="filter.value"-->
<!--                      :min="filter.min_value"-->
<!--                      :max="filter.max_value"-->
<!--                      :step="1"-->
<!--                      color="primary"-->
<!--                      class="q-px-md"-->
<!--                      :thumb-color="filter.color"-->
<!--                      :selection-color="filter.color"-->
<!--                      @update:model-value="ChangeCountFilter(filter.api_field, filter.value)"-->
<!--                    />-->
<!--                  </div>-->
<!--                </q-btn-dropdown>-->
<!--            </div>-->
<!--            <div v-for="filter in DATE_FILTERS" v-bind:key="filter.field" class="q-pr-md">-->
<!--              <q-btn-dropdown-->
<!--                  outline-->
<!--                  icon="calendar_today"-->
<!--                  :label="filter.name"-->
<!--                  text-color="grey-8"-->
<!--                  size="1.1em"-->
<!--              >-->
<!--                <div class="col">-->
<!--                  <div class="row tw-bg-slate-100 justify-between">-->
<!--                    <q-radio-->
<!--                      v-model="filter.toggle"-->
<!--                      :val="true"-->
<!--                      label="before"-->
<!--                      color="secondary"-->
<!--                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                    />-->
<!--                    <q-radio-->
<!--                      v-model="filter.toggle"-->
<!--                      :val="false"-->
<!--                      label="after"-->
<!--                      color="secondary"-->
<!--                      left-label-->
<!--                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                    />-->
<!--&lt;!&ndash;                    <q-toggle&ndash;&gt;-->
<!--&lt;!&ndash;                      :label="filter.toggle?'before the date':'after the date'"&ndash;&gt;-->
<!--&lt;!&ndash;                      color="primary"&ndash;&gt;-->
<!--&lt;!&ndash;                      v-model="filter.toggle"&ndash;&gt;-->
<!--&lt;!&ndash;                      class="q-pa-sm"&ndash;&gt;-->
<!--&lt;!&ndash;                      @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"&ndash;&gt;-->
<!--&lt;!&ndash;                    />&ndash;&gt;-->

<!--                  </div>-->
<!--                  <div class="row tw-bg-slate-100">-->
<!--                    <div class="q-gutter-sm">-->
<!--                      <q-radio v-model="filter.experimentrun_status" val="success" label="Success" color="positive" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                      <q-radio v-model="filter.experimentrun_status" val="all" label="All" color="secondary" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                      <q-radio v-model="filter.experimentrun_status" val="failed" label="Failed" color="negative" @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"/>-->
<!--                    </div>-->
<!--                  </div>-->
<!--                  <q-date-->
<!--                    v-model="filter.selected_date"-->
<!--                    @update:model-value="ChangeDateFilter(filter.api_field, filter.selected_date, filter.toggle, filter.experimentrun_status)"-->
<!--                    class="row q-pa-sm"-->
<!--                  />-->
<!--                </div>-->
<!--              </q-btn-dropdown>-->
<!--            </div>-->
<!--          </div>-->
<!--          <div class="col-auto">-->
<!--            <q-btn-->
<!--              label="clear filters"-->
<!--              icon="clear"-->
<!--              rounded-->
<!--              @click="ClearFilters()"-->
<!--            />-->
<!--          </div>-->
<!--        </div>-->
      </div>
    </template>  </q-table>
</template>

<script lang="ts">
import {onMounted, ref, watch} from 'vue';
import axios from 'axios';
import {CustomQTableColumn, convertToQTableColumn} from 'src/datatypes/quasar_extensions';
import {QTableColumn, QTablePagination} from 'src/datatypes/quasar';


export default {
  name: 'DataTable',
  props: {
    title: String,
    columns: Array as () => CustomQTableColumn[],
    pagination: {
      type: Object,
      default: () => ({
        sortBy: 'desc',
        descending: false,
        page: 1,
        rowsPerPage: 8,
        rowsNumber: 10,
      }),
    },
    api: String,
  },


  setup(props) {
    const rows = ref([]);
    const loading = ref(false);
    const mutablePagination = ref<QTablePagination>(props.pagination);
    const visibleColumns = ref<Array<CustomQTableColumn>>(props.columns.filter((c: any) => c.visible).map((c: any) => c));

    const loadTableData = async () => {
      loading.value = true;
      const { page, rowsPerPage, sortBy, descending } = mutablePagination.value;
      const offset = (page - 1) * rowsPerPage;
      let url = `${props.api}?limit=${rowsPerPage}&offset=${offset}`;

      if (sortBy) {
        url += `&ordering=${descending ? '-' : ''}${sortBy}`;
      }

      try {
        const response = await axios.get(url);
        mutablePagination.value.rowsNumber = response.data.count;
        rows.value = response.data.results;
      } catch (error) {
        console.error('Failed to load table data:', error);
        // handle error (e.g., show notification)
      } finally {
        loading.value = false;
      }
    };

    onMounted(loadTableData);

    return {
      rows,
      loading,
      visibleColumns,
      mutablePagination,
    };
  },
};
</script>
