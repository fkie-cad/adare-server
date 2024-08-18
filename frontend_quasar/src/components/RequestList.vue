<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :api="api" />
  </div>
</template>


<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn } from 'src/datatypes/quasar_extensions';
import API from 'src/api';


const title = 'Requests';

const columns: CustomQTableColumn[] = [
  { name: 'object.name', label: 'object', field: 'object.name', align: 'left', sortable: true, visible: true},
  { name: 'objective_name', label: 'type', field: 'objective_name', align: 'left', sortable: true, visible: true},
  { name: 'action', label: 'action', field: 'action', align: 'left', sortable: true, visible: true},
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: true, visible: true},
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: true, visible: true},
  { name: 'requester', label: 'requested by', field: 'requester', align: 'left', sortable: true, visible: true},
  { name: 'assignees', label: 'assignees', field: 'assignees', align: 'left', sortable: true, visible: true},
  { name: 'reviewers', label: 'reviewers', field: 'reviewers', align: 'left', sortable: true, visible: true},
  { name: 'last_change_date', label: 'last changed', field: 'last_change_date', align: 'left', sortable: true, visible: true},
  { name: 'creation_date', label: 'created at', field: 'creation_date', align: 'left', sortable: true, visible: true},

]

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

const api = API.API + 'request';

export default {
  name: 'RequestList',
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
