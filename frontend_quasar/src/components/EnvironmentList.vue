<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :store="environmentStore" />
  </div>
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import DataTableTags from 'components/datatable/DataTableTags.vue';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableOsInfo from 'components/datatable/DataTableOsInfo.vue';
import DataTableLink from 'components/datatable/DataTableLink.vue';
import { useEnvironmentStore } from 'src/store/environment';

const title = 'Environments';

const typeVarsLink = {
  icon: 'open_in_new',
  tooltip: 'go to gitea',
  color: 'primary',
}

const columns: CustomQTableColumn[] = [
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true, visible: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true, visible: true},
  { name: 'ulid', align: 'left', label: 'ulid', field: 'ulid', hideable: true, visible: true},
  { name: 'vagrantbox', align: 'left', label: 'box', field: 'vagrantbox', hideable: true, visible: true},
  { name: 'published_by', align: 'left', label: 'published by', field: 'published_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'created_by', align: 'left', label: 'created by', field: 'created_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'published_at', align: 'left', label: 'publish date', field: 'published_at', hideable: true, visible: true},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, visible: true, type: DataTableTags},
  { name: 'os_info', align: 'left', label: 'os', field: 'os_info', hideable: true, visible: true, type: DataTableOsInfo},
  { name: 'postsetup_installations', align: 'left', label: 'installations', field: 'postsetup_installations', hideable: true, visible: true},
  { name: 'file', align: 'left', label: 'file', field: 'file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
]

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

const api = 'environment';

export default {
  name: 'EnvironmentList',
  components: { DataTable },
  setup() {
    const environmentStore = useEnvironmentStore();

    return {
      environmentStore,
      title,
      columns,
      pagination,
      api
    };
  },
}

</script>
