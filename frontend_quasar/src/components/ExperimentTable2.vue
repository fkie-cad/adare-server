<template>
  <DataTable :title="title" :columns="columns" :pagination="pagination" :selectFilters="selectFilters" :api="api" />
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn, TypeVarsDetails } from 'src/datatypes/quasar_extensions';
import API from 'src/api';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableDetails from 'components/datatable/DataTableDetails.vue';
import DataTableLink from 'components/datatable/DataTableLink.vue';
import DataTableRunCounts from 'components/datatable/DataTableRunCounts.vue';
import DataTableTags from 'components/datatable/DataTableTags.vue';

const title = 'Experiments';

function link_to_experiment(uuid: string | undefined) {
  if (!uuid) {
    return '';
  }
  return '/experimentdetails/' + uuid;
}

const typeVarsDetails: TypeVarsDetails = {
  icon: 'o_add_circle',
  formatter: link_to_experiment,
  field: 'uuid',
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
  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true, visible: true},
  { name: 'published_by', align: 'left', label: 'publisher', field: 'published_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'published_at', align: 'left', label: 'publish date', field: 'published_at', hideable: true, visible: true},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, visible: true, type: DataTableTags},
  { name: 'run_counts', align: 'left', label: 'run counts', field: 'run_counts', hideable: true, visible: true, type: DataTableRunCounts},
  { name: 'action_file', align: 'left', label: 'action file', field: 'action_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'testset_file', align: 'left', label: 'testset file', field: 'testset_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'metadata_file', align: 'left', label: 'metadata file', field: 'metadata_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
]

const selectFilters = [
  { name: 'tags', field: 'tags', api_field: 'tags_mc', option_api_field: 'tags', type: 'options_mc', options: [] as string[], total_options: [] as string[], selected: []},
]

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

const api = API.API + 'experiment';

export default {
  name: 'ExperimentTable2',
  components: { DataTable },
  setup(props) {
    return {
      title,
      columns,
      pagination,
      selectFilters,
      api
    };
  },
}

</script>
