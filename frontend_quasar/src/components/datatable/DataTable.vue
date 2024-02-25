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
      <DataTablePanel
        :columns="columns"
        :visible-columns="visibleColumns"
        :table-props="props"
        :select-filters=selectFilters
        @update-visibleColumns="updateVisibleColumns"
        @update-filter="updateFilter"
        :api=api
      />
    </template>
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td
          v-for="col in props.cols"
          :key="col.field"
        >
          <div v-if="col.type">
            <component :is="col.type" :data="props.row[col.field]" :row="props.row" :col="col"
            />
          </div>
          <div v-else>
            {{ props.row[col.field] }}
          </div>

        </q-td>
      </q-tr>
    </template>
  </q-table>
</template>

<script lang="ts">
import {onMounted, ref} from 'vue';
import axios from 'axios';
import {CustomQTableColumn} from 'src/datatypes/quasar_extensions';
import {QTablePagination} from 'src/datatypes/quasar';
import DataTablePanel from 'components/datatable/DataTablePanel.vue';
import { Filter, FilterToQueryString } from 'src/datatypes/advancedtable';


export default {
  name: 'DataTable',
  components: { DataTablePanel },
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
    selectFilters: {
      type: Array,
      default: () => [],
      required: false,
    },
  },


  setup(props) {
    const rows = ref([]);
    const loading = ref(false);
    const mutablePagination = ref<QTablePagination>(props.pagination);
    // set visible columns to those that are initially visible or those who can not be hidden
    const visibleColumns = ref<Array<string>>(props.columns.filter((c: any) => c.visible).map((c: any) => c.field));
    const filterString = ref('');

    const loadTableData = async () => {
      loading.value = true;
      const { page, rowsPerPage, sortBy, descending } = mutablePagination.value;
      const offset = (page - 1) * rowsPerPage;
      let url = `${props.api}?limit=${rowsPerPage}&offset=${offset}`;

      if (sortBy) {
        url += `&ordering=${descending ? '-' : ''}${sortBy}`;
      }
      if (filterString.value) {
        url += `${filterString.value}`;
      }

      try {
        const response = await axios.get(url);
        console.log(url)
        console.log(response.data)
        mutablePagination.value.rowsNumber = response.data.count;
        rows.value = response.data.results;
      } catch (error) {
        console.error('Failed to load table data:', error);
        // handle error (e.g., show notification)
      } finally {
        loading.value = false;
      }
    };

    function updateVisibleColumns(visible_columns: string[]) {
      visibleColumns.value = visible_columns;
    }

    function updateFilter(filter: Filter) {
      filterString.value = FilterToQueryString(filter);
      loadTableData();
    }

    onMounted(loadTableData);

    return {
      rows,
      loading,
      visibleColumns,
      mutablePagination,
      updateVisibleColumns,
      updateFilter,
    };
  },
};
</script>
