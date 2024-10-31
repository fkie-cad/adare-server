<template>
  <q-table
    :title="title"
    :rows="store.getRows()"
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
        :store=store
      />
    </template>
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td
          v-for="col in props.cols"
          :key="col.field"
        >
          <div v-if="col.type">
            <component :is="col.type" :data="props.row[col.field.split('.')[0]][col.field.split('.')[1]]" :row="props.row" :col="col" v-if="col.field.includes('.')"/>
            <component :is="col.type" :data="props.row[col.field]" :row="props.row" :col="col" v-else/>
          </div>
          <div v-else-if="col.field.includes('.')">
            {{ props.row[col.field.split('.')[0]][col.field.split('.')[1]] }}
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
import { onMounted, ref } from 'vue';
import {CustomQTableColumn} from 'src/models/quasar_extensions';
import {QTablePagination} from 'src/models/quasar';
import DataTablePanel from 'components/datatable/DataTablePanel.vue';
import { Filter, FilterToQueryString, SelectFilter } from 'src/models/advancedtable';


export default {
  name: 'DataTable',
  components: { DataTablePanel },
  props: {
    title: {
      type: String,
      required: true,
    },
    columns: {
      type: Array as () => Array<CustomQTableColumn>,
      required: true,
    },
    pagination: {
      type: Object as () => QTablePagination,
      default: () => ({
        sortBy: 'desc',
        descending: false,
        page: 1,
        rowsPerPage: 8,
        rowsNumber: 10,
      }),
    },
    store: {
      type: Object,
      required: true,
    },
    selectFilters: {
      type: Array as () => Array<SelectFilter>,
      default: () => [],
      required: false,
    },
  },


  setup(props) {
    const loading = ref<boolean>(false);
    const mutablePagination = ref<QTablePagination>(props.pagination);

    const visibleColumns = ref<string[]>(
      props.columns
        .filter((c: CustomQTableColumn) => c.visible)
        .map((c: CustomQTableColumn) => c.field) as string[]
    );

    const filterString = ref('');

    function updateVisibleColumns(visible_columns: string[]) {
      visibleColumns.value = visible_columns;
    }

    function updateFilter(filter: Filter) {
      filterString.value = FilterToQueryString(filter);
    }

    onMounted(async () => {
      loading.value = true;
      const offset = (mutablePagination.value.page - 1) * mutablePagination.value.rowsPerPage;
      await props.store.fetchRowsAdvanced(
        mutablePagination.value.rowsPerPage,
        offset,
        mutablePagination.value.sortBy,
        mutablePagination.value.descending,
      );
      loading.value = false;
    });

    return {
      loading,
      visibleColumns,
      mutablePagination,
      updateVisibleColumns,
      updateFilter,
    };
  },
};
</script>
