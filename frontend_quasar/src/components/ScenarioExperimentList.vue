<template>
  <div
    class="tw-w-5/6"
  >
    <AdvancedDataTable
      title="Experiments"
      :data_filter_function=ExperimentStore.FilterExperimentListRemote
      :data_get_function=ExperimentStore.GetExperimentList
      :data_load_function=load_experiments_func
      :visible-columns=vis_columns
      :columns=columns
      class="tw-w-full"
    />
  </div>
</template>


<script lang="ts">
import { useExperimentStore } from 'stores/experiments';
import AdvancedDataTable from 'components/global/AdvancedDataTable.vue';
import {storeToRefs} from 'pinia';

const columns = [
  { name: 'details', label: 'details', field: 'details', align: 'left', hideable: true, non_api_field: true, type: 'link', link_field: 'uuid', link_url: '/experiment/', link_icon: 'o_add_circle'},
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true},
  { name: 'uuid', align: 'left', label: 'uuid', field: 'uuid', hideable: true},
  { name: 'publisher_name', align: 'left', label: 'publisher', field: 'publisher_name', hideable: true, type: 'user_icon'},
  { name: 'publish_date', align: 'left', label: 'publish date', field: 'publish_date', hideable: true},
  { name: 'tags', align: 'left', label: 'tags', field: 'tags', hideable: true, type: 'tags'},
  { name: 'run_counts', align: 'left', label: 'run counts', field: 'run_counts', hideable: true, type:'run_counts'},
]

const vis_columns = ['details', 'name', 'description', 'publisher_name', 'tags', 'run_counts']


export default {
  name: 'ScenarioExperimentList',
  components: {AdvancedDataTable},

  props: {
    uuid: {
      type: String,
      required: true
    }
  },

  setup(props) {
    let ExperimentStore = useExperimentStore()
    storeToRefs(ExperimentStore)

    const load_experiments_func = () => { return ExperimentStore.LoadExperimentByScenario(props.uuid)}

    return {
      ExperimentStore,
      load_experiments_func,
      columns,
      vis_columns,
    }
  }
}

</script>
