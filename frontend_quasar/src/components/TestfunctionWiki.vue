<template>
  <div
    class="tw-w-5/6"
  >
  <AdvancedDataTable
    title="Testfunctions"
    :data_get_function=TestfunctionStore.GetTestfunctions
    :data_load_function=TestfunctionStore.LoadTestfunctionsAll
    :data_filter_function=TestfunctionStore.FilterTestfunctions
    :columns=columns
    class="tw-w-full"
  />
  </div>
</template>


<script lang="ts">
import {ref} from 'vue';
import { useTestfunctionStore } from 'stores/testfunction';
import { storeToRefs } from 'pinia';
import AdvancedDataTable from 'components/global/AdvancedDataTable.vue';

let columns = [
  { name: 'name', align: 'left', label: 'name', field: 'name', sortable: true },
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true },
  { name: 'possible_parameters', align: 'left', label: 'possible parameters', field: 'possible_parameters', hideable: true, type: 'expand' },
]

export default {
  name: 'TestfunctionWiki',
  components: {AdvancedDataTable},

  setup() {
    let TestfunctionStore = useTestfunctionStore()
    storeToRefs(TestfunctionStore)


    return {
      TestfunctionStore,
      columns,
    }
  }
}

</script>
