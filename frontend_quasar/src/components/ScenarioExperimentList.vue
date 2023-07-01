<template>
  <div
    class="tw-w-5/6"
  >
    <AdvancedDataTable
      title="Experiments"
      :data_filter_function=ScenarioStore.FilterExperimentListRemote
      :data_get_function=ScenarioStore.GetExperimentList
      :data_load_function=load_experiments_func
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
]

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
    let ScenarioStore = useScenarioStore()

    const load_experiments_func = () => { return ScenarioStore.LoadExperimentByScenario(props.uuid)}

    onMounted(() => {
      console.log(props.uuid)
    })

    return {
      ScenarioStore,
      load_experiments_func,
      columns: columns,
      visibleColumns: ref(['name', 'uuid', 'publisher_name', 'tags'])
    }
  }
}

</script>
