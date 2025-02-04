<template>
  <div v-if="experiment">
    <q-card>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">ulid</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col flex justify-start">
            <div>
              {{experiment.name}}
            </div>
            <q-btn
              color="secondary"
              icon="open_in_new"
              class="q-px-sm q-mb-auto q-ml-xs"
              size="xs"
              style="top: -0.4rem;"
              @click="OpenExperimentInNewTab"
            >
              <q-tooltip>
                open experiment in gitea
              </q-tooltip>
            </q-btn>
          </div>
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
      <q-card-section v-if="experiment.tags">
        <div class="row tw-text-gray-600">
          <div class="col">tags</div>
          <div class="col tw-text-right">run counts</div>
        </div>
        <div class="row">
          <div class="col">
            <q-badge
              v-for="item in experiment.tags"
              :key="item.name"
              color="pink-9"
              class="q-ma-xs tw-text-sm"
            >
              #{{ item }}
            </q-badge>
          </div>
          <div class="col tw-text-right">
            <q-badge color="positive" class="q-ma-sm q-px-sm tw-text-xl">
              {{ experiment.run_counts.successful }}
            </q-badge>
            <q-badge color="negative" class="q-ma-sm q-px-sm tw-text-xl">
              {{ experiment.run_counts.failed }}
            </q-badge>
          </div>
        </div>
      </q-card-section>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">created by</div>
          <div class="col tw-text-right">published by</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">
            <ProfileImage
              :profile="createdByProfile"
              size="md"
              :tooltip=true
              :linkToProfile=true
              v-if=createdByProfile
            />
          </div>
          <div class="col tw-text-right flex justify-end">
            <ProfileImage
              :profile="publishedByProfile"
              size="md"
              :tooltip=true
              :linkToProfile=true
              v-if=publishedByProfile
            />
          </div>
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
import { useUserStore } from 'src/store/user';
import { computed, onMounted } from 'vue';
import DataTable from 'components/datatable/DataTable.vue';
import { useExperimentTestsStore } from 'src/store/experimentests';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import DataTableParameter from 'components/datatable/DataTableParameter.vue';
import DataTableTestfunction from 'components/datatable/DataTableTestfunction.vue';
import ProfileImage from 'components/ProfileImage.vue';

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

  components: { ProfileImage, DataTable },

  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const experimentStore = useExperimentStore()
    const userStore = useUserStore()
    const experimentTestsStore = useExperimentTestsStore()
    const experiment = computed(() => experimentStore.getExperimentByName(props.name))
    const createdByProfile = computed(() => experiment.value ? userStore.getProfile(experiment.value.created_by) : undefined);
    const publishedByProfile = computed(() => experiment.value ? userStore.getProfile(experiment.value.published_by) : undefined);

    function OpenExperimentInNewTab(){
      let url = experiment.value?.action_file?.split('/').slice(0, -1).join('/')
      window.open(url, '_blank')
    }

    onMounted(async () => {
      await experimentStore.loadExperimentByName(props.name)
      if (!experiment.value) {
        return
      }
      await experimentTestsStore.setExperiment(experiment.value.name)
      await userStore.fetchProfile(experiment.value.created_by)
    })

    return {
      experiment,
      experimentTestsStore,
      columns_test,
      createdByProfile,
      OpenExperimentInNewTab,
      publishedByProfile,
    }
  }
}

</script>
