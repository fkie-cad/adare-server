<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :api="api" />
  </div>
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn } from 'src/datatypes/quasar_extensions';
import API from 'src/api';
import DataTableTags from 'components/datatable/DataTableTags.vue';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableOsInfo from 'components/datatable/DataTableOsInfo.vue';
import DataTableLink from 'components/datatable/DataTableLink.vue';


const title = 'Experiment Runs';

const typeVarsLink = {
  icon: 'open_in_new',
  tooltip: 'go to gitea',
  color: 'primary',
}

const columns: CustomQTableColumn[] = [
  { name: 'ulid', align: 'left', label: 'ulid', field: 'ulid', hideable: true, visible: true},
  { name: 'experiment', align: 'left', label: 'experiment', field: 'experiment', hideable: true, visible: true},
  { name: 'status', align: 'left', label: 'status', field: 'status', hideable: true, visible: true},
]

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

const api = API.API + 'run';

export default {
  name: 'RunList',
  components: { DataTable },
  setup(props) {
    return {
      title,
      columns,
      pagination,
      api
    };
  },
}

</script>
