<template>
  <div v-if="experiment">
    <q-card>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">ulid</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{experiment.name}}</div>
          <div class="col tw-text-right">{{experiment.ulid}}</div>
        </div>
      </q-card-section>
      <q-card-section v-if="experiment.description">
        <div class="row tw-text-gray-600">
          <div class="col">description</div>
        </div>
        <div class="row">
          <div class="col">{{experiment.description}}</div>
        </div>
      </q-card-section>
      <q-card-section>
        <DataTable title="Tests" :store="experimentTestsStore" :columns="columns_test" />
      </q-card-section>
    </q-card>
  </div>
  <div v-else>
    <q-card>
      <q-card-section>
        <div class="text-h6">Experiment not found</div>
      </q-card-section>
    </q-card>
  </div>
</template>


<script lang="ts">
import { useExperimentStore } from 'src/store/experiment';
import { onMounted, ref } from 'vue';
import { Experiment } from 'src/models/experiment';
import DataTable from 'components/datatable/DataTable.vue';
import { useExperimentTestsStore } from 'src/store/experimentests';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import DataTableParameter from 'components/datatable/DataTableParameter.vue';
import DataTableTestfunction from 'components/datatable/DataTableTestfunction.vue';

const columns_test: CustomQTableColumn[] = [
  { name: 'name', align: 'left', label: 'name', field: 'name', hideable: true, visible: true},
  // { name: 'testfunction.set', align: 'left', label: 'set', field: 'testfunction.set', hideable: true, visible: true},
  { name: 'ulid', align: 'left', label: 'ulid', field: 'ulid', hideable: true, visible: false},
  { name: 'description', align: 'left', label: 'description', field: 'description', hideable: true, visible: true},
  { name: 'testfunction', align: 'left', label: 'testfunction', field: 'testfunction', hideable: true, visible: true, type: DataTableTestfunction},
  { name: 'parameters', align: 'left', label: 'parameters', field: 'parameters', hideable: true, visible: true, type: DataTableParameter},
]

export default {
  name: 'ExperimentOverview',

  components: { DataTable },

  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    let experimentStore = useExperimentStore()
    const experimentTestsStore = useExperimentTestsStore()
    let experiment = ref<Experiment>()

    onMounted(async () => {
      const exp = await experimentStore.loadExperimentByName(props.name)
      if (exp) {
        experiment.value = exp
      }
      await experimentTestsStore.setExperiment(exp.name)
    })

    return {
      experiment,
      experimentTestsStore,
      columns_test,
    }
  }
}

</script>
