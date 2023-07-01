<template>
  <div
    class="tw-w-5/6"
  >
    <AdvancedDataTable
      title="Experiments"
      :data_filter_function=ScenarioStore.FilterExperimentListRemote
      :data_get_function=ScenarioStore.GetExperimentList
      :data_load_function=ScenarioStore.LoadExperimentAll
      :visible-columns=visibleColumns
      :columns=columns
      class="tw-w-full"
    />
  </div>
</template>


<script lang="ts">
import {onMounted, ref} from 'vue';
import { useScenarioStore } from 'stores/scenario';
import AdvancedDataTable from 'components/global/AdvancedDataTable.vue';

const columns = [
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true},
  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true},
  { name: 'publisher_name', align: 'left', label: 'publisher', field: 'publisher_name', hideable: true, type: 'user_icon'},
  { name: 'publish_date', align: 'left', label: 'publish date', field: 'publish_date', hideable: true},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, type: 'tags'},
  { name: 'run_counts', align: 'left', label: 'run counts', field: 'run_counts', hideable: true, type:'run_counts'}
]

export default {
  name: 'ScenarioExperimentList',
  components: {AdvancedDataTable},

  setup() {
    let ScenarioStore = useScenarioStore()

    return {
      ScenarioStore,
      columns: columns,
      visibleColumns: ref(['name', 'uuid', 'publisher_name', 'tags'])
    }
  }
}

</script>
