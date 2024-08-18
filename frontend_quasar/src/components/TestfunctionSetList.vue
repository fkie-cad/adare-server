<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :api="api" />
  </div>
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn, TypeVarsDetails } from 'src/datatypes/quasar_extensions';
import API from 'src/api';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableLink from 'components/datatable/DataTableLink.vue';
import DataTableDetails from 'components/datatable/DataTableDetails.vue';

const title = 'Testfunction Sets';

function link_to_experiment(ulid: string | undefined) {
  if (!ulid) {
    return '';
  }
  return '/testfunctiondetails/' + ulid;
}

const typeVarsDetails: TypeVarsDetails = {
  icon: 'o_add_circle',
  formatter: link_to_experiment,
  field: 'ulid',
}

const typeVarsLink = {
  icon: 'open_in_new',
  tooltip: 'go to gitea',
  color: 'primary',
}

const columns: CustomQTableColumn[] = [
  { name: 'details', label: 'details', field: 'details', align: 'left', hideable: true, visible: true, type: DataTableDetails, typeVarsDetails: typeVarsDetails},
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true, visible: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true, visible: true},
  { name: 'published_by', align: 'left', label: 'published by', field: 'published_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'published_at', align: 'left', label: 'published at', field: 'published_at', hideable: true, visible: true},
  { name: 'accepted_by', align: 'left', label: 'accepted by', field: 'accepted_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'file', align: 'left', label: 'file', field: 'file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'requirements_file', align: 'left', label: 'requirements_file', field: 'requirements_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'num_testfunctions', align: 'left', label: '# testfunctions', field: 'num_testfunctions', hideable: true, visible: true},
]



const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

const api = API.API + 'testfunction';

export default {
  name: 'TestfunctionSetList',
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
