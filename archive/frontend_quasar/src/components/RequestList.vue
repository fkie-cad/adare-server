<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :store="requestStore" />
  </div>
</template>


<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn, TypeVarsTag } from 'src/models/quasar_extensions';
import DataTableTags from 'components/datatable/DataTableTags.vue';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableUserIconList from 'components/datatable/DataTableUserIconList.vue';
import { useRequestStore } from 'src/store/request';

const title = 'Requests';

const typeVarsTag: TypeVarsTag = {
  color: 'secondary',
}

const columns: CustomQTableColumn[] = [
  { name: 'object_name', label: 'object', field: 'object_name', align: 'left', sortable: true, visible: true},
  { name: 'objective_name', label: 'type', field: 'objective_name', align: 'left', sortable: true, visible: true},
  { name: 'action', label: 'action', field: 'action', align: 'left', sortable: true, visible: true},
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: true, visible: true},
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: true, visible: true, type: DataTableTags, typeVarsTag: typeVarsTag},
  { name: 'requester', label: 'requested by', field: 'requester', align: 'left', sortable: true, visible: true, type: DataTableUserIcon},
  { name: 'assignees', label: 'assignees', field: 'assignees', align: 'left', sortable: true, visible: true, type: DataTableUserIconList},
  { name: 'reviewers', label: 'reviewers', field: 'reviewers', align: 'left', sortable: true, visible: true, type: DataTableUserIconList},
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

const api = 'request';

export default {
  name: 'RequestList',
  components: { DataTable },
  setup() {
    const requestStore = useRequestStore();

    return {
      requestStore,
      title,
      columns,
      pagination,
      api
    };
  },
}

</script>
