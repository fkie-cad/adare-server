<template>
  <div>
      <DataTable :title="title" :columns="columns" :pagination="pagination" :selectFilters="selectFilters" :store="experimentStore" />
  </div>
</template>

<script lang="ts">
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn, TypeVarsDetails } from 'src/models/quasar_extensions';
import { SelectFilter } from 'src/models/advancedtable';
import DataTableUserIcon from 'components/datatable/DataTableUserIcon.vue';
import DataTableDetails from 'components/datatable/DataTableDetails.vue';
import DataTableLink from 'components/datatable/DataTableLink.vue';
import DataTableRunCounts from 'components/datatable/DataTableRunCounts.vue';
import DataTableTags from 'components/datatable/DataTableTags.vue';
import { useExperimentStore } from 'src/store/experiment';

const title = 'Experiments';

function link_to_experiment(ulid: string | undefined) {
  if (!ulid) {
    return '';
  }
  return '/experiment/' + ulid;
}

const typeVarsDetails: TypeVarsDetails = {
  icon: 'o_add_circle',
  formatter: link_to_experiment,
  field: 'name',
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
  { name: 'ulid', align: 'left', label: 'ulid', field: 'ulid', hideable: true, visible: true},
  { name: 'published_by', align: 'left', label: 'published by', field: 'published_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'published_at', align: 'left', label: 'publish date', field: 'published_at', hideable: true, visible: true},
  { name: 'created_by', align: 'left', label: 'created by', field: 'created_by', hideable: false, visible: true, type: DataTableUserIcon},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, visible: true, type: DataTableTags},
  { name: 'run_counts', align: 'left', label: 'run counts', field: 'run_counts', hideable: true, visible: true, type: DataTableRunCounts},
  { name: 'action_file', align: 'left', label: 'action file', field: 'action_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'testset_file', align: 'left', label: 'testset file', field: 'testset_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
  { name: 'metadata_file', align: 'left', label: 'metadata file', field: 'metadata_file', hideable: true, visible: true, type: DataTableLink, typeVarsLink: typeVarsLink},
]

const selectFilters: SelectFilter[] = []

const pagination = {
  sortBy: 'desc',
  descending: false,
  page: 1,
  rowsPerPage: 8,
  rowsNumber: 10,
};

export default {
  name: 'ExperimentList',
  components: { DataTable },
  setup() {
    const experimentStore = useExperimentStore();

    return {
      experimentStore,
      title,
      columns,
      pagination,
      selectFilters,
    };
  },
}

</script>
