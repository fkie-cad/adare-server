<template>
  <div v-if="testfunctionSet" class="full-width q-pa-xl">
    <q-card
      class="full-width"
    >
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">published by</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{testfunctionSet.name}}</div>
          <div class="col flex justify-end"><ProfileImage :profile="publishedByProfile" v-if="publishedByProfile"/></div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md">
          <div class="col"># testfunctions</div>
          <div class="col tw-text-right">created by</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{testfunctionSet.num_testfunctions}}</div>
          <div class="col flex justify-end">
            <ProfileImage :profile="createdByProfile" v-if="createdByProfile"/>
            <div class="tw-text-3xl" v-else>-</div>
          </div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md" v-if="testfunctionSet.description">
          <div class="col">description</div>
          <div class="col tw-text-right"></div>
        </div>
        <div class="row  tw-text-3xl" v-if="testfunctionSet.description">
          <div class="col">{{testfunctionSet.description}}</div>
          <div class="col"></div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md">
          <div class="col">files</div>
          <div class="col tw-text-right"></div>
        </div>
        <div class="row tw-text-3xl">
          <div class="col">
            <q-btn
              color="primary"
              icon="open_in_new"
              @click="openGiteaTestfunctionSetDir"
            />
          </div>
          <div class="col"></div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <DataTable title="Testfunctions" :store="testfunctionStore" :columns="columns" />
      </q-card-section>
    </q-card>

    <!-- Cross-reference: Experiments using functions from this set -->
    <q-card class="q-mt-md" v-if="relatedExperiments.length > 0">
      <q-card-section>
        <div class="text-subtitle1 text-weight-bold q-mb-sm">
          Experiments Using These Functions
          <q-badge color="primary" class="q-ml-sm">{{ relatedExperiments.length }}</q-badge>
        </div>
        <q-markup-table flat dense separator="horizontal">
          <thead>
            <tr>
              <th class="text-left">Experiment</th>
              <th class="text-left">Tags</th>
              <th class="text-center">Runs</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exp in relatedExperiments" :key="exp.ulid">
              <td>
                <router-link :to="`/experiment/${exp.name}`" class="text-primary text-weight-medium">
                  {{ exp.name }}
                </router-link>
              </td>
              <td>
                <ScopedTagBadge v-for="tag in exp.tags.slice(0, 3)" :key="tag.name" :tag="tag" />
              </td>
              <td class="text-center">
                <q-badge color="positive" class="q-mr-xs">{{ exp.run_counts.successful }}</q-badge>
                <q-badge color="negative">{{ exp.run_counts.failed }}</q-badge>
              </td>
            </tr>
          </tbody>
        </q-markup-table>
      </q-card-section>
    </q-card>
  </div>
  <div v-else>
    <h1>
      Testfunction with name {{ name }} not found
    </h1>
  </div>
</template>

<script lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useTestfunctionSetStore } from 'src/store/testfunctionset';
import { useTestfunctionStore } from 'src/store/testfunction';
import { useExperimentStore } from 'src/store/experiment';
import { useUserStore } from 'src/store/user';
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import ProfileImage from 'components/ProfileImage.vue';
import DataTableAbstractParameter from 'components/datatable/DataTableAbstractParameter.vue';
import ScopedTagBadge from 'components/global/ScopedTagBadge.vue';
import { Experiment } from 'src/models/experiment';

const columns: CustomQTableColumn[] = [
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true, visible: true, hideable: true},
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: true, visible: true, hideable: true},
  { name: 'possible_parameters', label: 'possible_parameters', field: 'possible_parameters', align: 'left', sortable: true, visible: true, hideable: true, type: DataTableAbstractParameter},
]


export default {
  name: 'TestfunctionSetDetail',
  components: { DataTable, ProfileImage, ScopedTagBadge },
  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const store = useTestfunctionSetStore();
    const testfunctionStore = useTestfunctionStore();
    const experimentStore = useExperimentStore();
    const userStore = useUserStore();
    testfunctionStore.setTestfunctionSet(props.name);
    const testfunctionSet = computed(() => store.getTestfunctionSet(props.name));
    const publishedByProfile = computed(() => testfunctionSet.value ? userStore.getProfile(testfunctionSet.value.published_by) : undefined);
    const createdByProfile = computed(() => testfunctionSet.value ? userStore.getProfile(testfunctionSet.value.created_by) : undefined);
    const relatedExperiments = ref<Experiment[]>([]);

    const openGiteaTestfunctionSetDir = () => {
      const file = testfunctionSet.value?.file
      const parentDir = file?.split('/').slice(0, -1).join('/')
      window.open(parentDir, '_blank')
    }

    onMounted(async () => {
      await store.fetchTestfunctionSets('');
      if (testfunctionSet.value) {
        await userStore.fetchProfile(testfunctionSet.value.published_by);
      }

      // Fetch experiments using functions from this set
      try {
        await experimentStore.fetchExperimentsAdvanced(
          20, 0, 'published_at', true, undefined,
          { testfunction_set: props.name }
        );
        relatedExperiments.value = experimentStore.getRows();
      } catch (e) {
        // Experiments not available
      }
    });

    return {
      columns,
      testfunctionStore,
      testfunctionSet,
      publishedByProfile,
      createdByProfile,
      openGiteaTestfunctionSetDir,
      relatedExperiments,
    };
  }
};
</script>
