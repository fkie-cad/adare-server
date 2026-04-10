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
            <ScopedTagBadge
              v-for="item in experiment.tags"
              :key="item.name"
              :tag="item"
              class="tw-text-sm"
            />
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

    <!-- Environments used by this experiment -->
    <q-card class="q-mt-md" v-if="experiment.environments && experiment.environments.length > 0">
      <q-card-section>
        <div class="text-subtitle1 text-weight-bold q-mb-sm">
          Environments
          <q-badge color="primary" class="q-ml-sm">{{ experiment.environments.length }}</q-badge>
        </div>
        <q-markup-table flat dense separator="horizontal">
          <thead>
            <tr>
              <th class="text-left">Name</th>
              <th class="text-left">OS</th>
              <th class="text-left">Vagrant Box</th>
              <th class="text-left">Tags</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="env in experiment.environments" :key="env.ulid">
              <td>
                <router-link :to="`/environment/${env.name}`" class="text-primary text-weight-medium">
                  {{ env.name }}
                </router-link>
              </td>
              <td>{{ env.os_info?.distribution }} {{ env.os_info?.version }}</td>
              <td>{{ env.vagrantbox }}</td>
              <td>
                <ScopedTagBadge v-for="tag in env.tags.slice(0, 3)" :key="tag.name" :tag="tag" />
              </td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card-section>
    </q-card>

    <!-- Recent Runs -->
    <q-card class="q-mt-md" v-if="recentRuns.length > 0">
      <q-card-section>
        <div class="text-subtitle1 text-weight-bold q-mb-sm">
          Recent Runs
          <q-badge color="primary" class="q-ml-sm">{{ recentRuns.length }}</q-badge>
        </div>
        <q-markup-table flat dense separator="horizontal">
          <thead>
            <tr>
              <th class="text-left">ULID</th>
              <th class="text-left">Environment</th>
              <th class="text-left">Result</th>
              <th class="text-left">Duration</th>
              <th class="text-left">Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in recentRuns" :key="run.ulid">
              <td>
                <router-link :to="`/run/${run.ulid}`" class="text-primary">
                  {{ run.ulid.substring(0, 10) }}...
                </router-link>
              </td>
              <td>{{ run.environment }}</td>
              <td>
                <q-badge :color="run.result_status?.name === 'success' ? 'positive' : 'negative'">
                  {{ run.result_status?.name }}
                </q-badge>
              </td>
              <td>{{ run.duration ? formatDuration(run.duration) : '-' }}</td>
              <td>{{ run.published_at }}</td>
            </tr>
          </tbody>
        </q-markup-table>
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
import { useRunStore } from 'src/store/run';
import { computed, ref, onMounted } from 'vue';
import DataTable from 'components/datatable/DataTable.vue';
import { useExperimentTestsStore } from 'src/store/experimentests';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import DataTableParameter from 'components/datatable/DataTableParameter.vue';
import DataTableTestfunction from 'components/datatable/DataTableTestfunction.vue';
import ProfileImage from 'components/ProfileImage.vue';
import ScopedTagBadge from 'components/global/ScopedTagBadge.vue';
import { Run } from 'src/models/experiment';

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

  components: { ProfileImage, DataTable, ScopedTagBadge },

  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const experimentStore = useExperimentStore()
    const userStore = useUserStore()
    const runStore = useRunStore()
    const experimentTestsStore = useExperimentTestsStore()
    const experiment = computed(() => experimentStore.getExperimentByName(props.name))
    const createdByProfile = computed(() => experiment.value ? userStore.getProfile(experiment.value.created_by) : undefined);
    const publishedByProfile = computed(() => experiment.value ? userStore.getProfile(experiment.value.published_by) : undefined);
    const recentRuns = ref<Run[]>([]);

    function OpenExperimentInNewTab(){
      let url = experiment.value?.action_file?.split('/').slice(0, -1).join('/')
      window.open(url, '_blank')
    }

    function formatDuration(duration: number) {
      if (!duration || duration < 0) return '-';
      const seconds = Math.floor(duration);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      if (hours > 0) return `${hours}h ${minutes % 60}m`;
      if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
      return `${seconds}s`;
    }

    onMounted(async () => {
      await experimentStore.loadExperimentByName(props.name)
      if (!experiment.value) {
        return
      }
      await experimentTestsStore.setExperiment(experiment.value.name)
      await userStore.fetchProfile(experiment.value.created_by)

      // Fetch recent runs for this experiment
      try {
        await runStore.fetchRunsAdvanced(5, 0, 'timestamp_start', true, props.name);
        recentRuns.value = runStore.getRows();
      } catch (e) {
        // Runs not available
      }
    })

    return {
      experiment,
      experimentTestsStore,
      columns_test,
      createdByProfile,
      OpenExperimentInNewTab,
      publishedByProfile,
      recentRuns,
      formatDuration,
    }
  }
}

</script>
