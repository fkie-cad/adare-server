<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :store="runStore"/>
  </div>
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn, TypeVarsDetails } from 'src/models/quasar_extensions';
import DataTableDetails from 'components/datatable/DataTableDetails.vue';
import DataTableStatus from 'components/datatable/DataTableStatus.vue';
import { useRunStore } from 'src/store/run';


const title = 'Experiment Runs';

function link_to_run(ulid: string | undefined) {
  if (!ulid) {
    return '';
  }
  return '/run/' + ulid;
}

const typeVarsDetails: TypeVarsDetails = {
  icon: 'o_add_circle',
  formatter: link_to_run,
  field: 'ulid',
}

const columns: CustomQTableColumn[] = [
  { name: 'result_status', align: 'left', label: '', field: 'result_status', hideable: true, visible: true, type: DataTableStatus},
  { name: 'experiment', align: 'left', label: 'experiment', field: 'experiment', hideable: true, visible: true},
  { name: 'environment', align: 'left', label: 'environment', field: 'environment', hideable: true, visible: true},
  { name: 'ulid', align: 'left', label: 'ulid', field: 'ulid', hideable: true, visible: true},
  { name: 'details', label: 'details', field: 'details', align: 'left', hideable: true, visible: true, type: DataTableDetails, typeVarsDetails: typeVarsDetails},
  // { name: 'result_status', align: 'left', label: 'result_status', field: 'result_status', hideable: true, visible: true, type: DataTableStatus},
]

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};


export default {
  name: 'RunList',
  components: { DataTable },
  setup() {
    const runStore = useRunStore();



    return {
      title,
      columns,
      pagination,
      runStore,
    };
  },
}

</script>
