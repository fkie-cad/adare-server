<template>
  <div v-if="environment">
    <!-- Header card -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">ulid</div>
        </div>
        <div class="row tw-text-3xl">
          <div class="col flex justify-start">
            <div>{{ environment.name }}</div>
            <q-btn
              v-if="environment.file"
              color="secondary"
              icon="open_in_new"
              class="q-px-sm q-mb-auto q-ml-xs"
              size="xs"
              style="top: -0.4rem;"
              @click="openInGitea"
            >
              <q-tooltip>open in gitea</q-tooltip>
            </q-btn>
          </div>
          <div class="col tw-text-right">{{ environment.ulid }}</div>
        </div>
      </q-card-section>

      <q-card-section v-if="environment.description">
        <div class="row tw-text-gray-600">
          <div class="col">description</div>
        </div>
        <div class="row">
          <div class="col">{{ environment.description }}</div>
        </div>
      </q-card-section>

      <q-card-section v-if="environment.tags && environment.tags.length > 0">
        <div class="row tw-text-gray-600">
          <div class="col">tags</div>
        </div>
        <div class="row">
          <div class="col">
            <ScopedTagBadge
              v-for="tag in environment.tags"
              :key="tag.name"
              :tag="tag"
              class="tw-text-sm"
            />
          </div>
        </div>
      </q-card-section>

      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">created by</div>
          <div class="col tw-text-right">published by</div>
        </div>
        <div class="row tw-text-3xl">
          <div class="col">
            <ProfileImage
              v-if="createdByProfile"
              :profile="createdByProfile"
              size="md"
              :tooltip="true"
              :linkToProfile="true"
            />
          </div>
          <div class="col tw-text-right flex justify-end">
            <ProfileImage
              v-if="publishedByProfile"
              :profile="publishedByProfile"
              size="md"
              :tooltip="true"
              :linkToProfile="true"
            />
          </div>
        </div>
      </q-card-section>

      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">vagrant box</div>
          <div class="col tw-text-right">published at</div>
        </div>
        <div class="row">
          <div class="col">
            <a :href="vagrantCloudUrl" target="_blank" class="text-primary">
              {{ environment.vagrantbox }}
            </a>
          </div>
          <div class="col tw-text-right">{{ environment.published_at }}</div>
        </div>
      </q-card-section>
    </q-card>

    <!-- OS Info + Post-setup installations -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-6">
        <q-card class="fit">
          <q-card-section>
            <div class="text-subtitle1 text-weight-bold q-mb-sm">Operating System</div>
            <q-markup-table flat dense separator="none">
              <tbody>
                <tr v-if="environment.os_info?.os">
                  <td class="text-grey-7" style="width: 120px;">OS</td>
                  <td class="text-weight-medium">{{ environment.os_info.os }}</td>
                </tr>
                <tr v-if="environment.os_info?.distribution">
                  <td class="text-grey-7">Distribution</td>
                  <td class="text-weight-medium">{{ environment.os_info.distribution }}</td>
                </tr>
                <tr v-if="environment.os_info?.version">
                  <td class="text-grey-7">Version</td>
                  <td class="text-weight-medium">{{ environment.os_info.version }}</td>
                </tr>
                <tr v-if="environment.os_info?.architecture">
                  <td class="text-grey-7">Architecture</td>
                  <td class="text-weight-medium">{{ environment.os_info.architecture }}</td>
                </tr>
                <tr v-if="environment.os_info?.language">
                  <td class="text-grey-7">Language</td>
                  <td class="text-weight-medium">{{ environment.os_info.language }}</td>
                </tr>
              </tbody>
            </q-markup-table>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-6">
        <q-card class="fit">
          <q-card-section>
            <div class="text-subtitle1 text-weight-bold q-mb-sm">Post-Setup Installations</div>
            <q-list dense v-if="environment.post_setup_installations && environment.post_setup_installations.length > 0">
              <q-item v-for="(install, idx) in environment.post_setup_installations" :key="idx">
                <q-item-section>
                  <q-item-label class="text-weight-medium">{{ install.name }}</q-item-label>
                  <q-item-label caption v-if="install.command">
                    <code>{{ install.command }}</code>
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-grey-6">No post-setup installations</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Cross-reference: Experiments using this environment -->
    <q-card>
      <q-card-section>
        <div class="row items-center justify-between q-mb-sm">
          <div class="text-subtitle1 text-weight-bold">
            Experiments Using This Environment
            <q-badge v-if="relatedExperiments.length > 0" color="primary" class="q-ml-sm">
              {{ relatedExperiments.length }}
            </q-badge>
          </div>
        </div>
        <q-markup-table flat dense separator="horizontal" v-if="relatedExperiments.length > 0">
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
        <div v-else class="text-grey-6">No experiments use this environment yet.</div>
      </q-card-section>
    </q-card>
  </div>

  <div v-else>
    <q-card>
      <q-card-section>
        <div class="text-h6">Environment not found</div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref, onMounted } from 'vue';
import { useEnvironmentStore } from 'src/store/environment';
import { useExperimentStore } from 'src/store/experiment';
import { useUserStore } from 'src/store/user';
import { Experiment } from 'src/models/experiment';
import ScopedTagBadge from 'src/components/global/ScopedTagBadge.vue';
import ProfileImage from 'src/components/ProfileImage.vue';

export default defineComponent({
  name: 'EnvironmentOverview',
  components: { ScopedTagBadge, ProfileImage },
  props: {
    name: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const environmentStore = useEnvironmentStore();
    const experimentStore = useExperimentStore();
    const userStore = useUserStore();

    const environment = computed(() => environmentStore.getEnvironmentByName(props.name));
    const relatedExperiments = ref<Experiment[]>([]);

    const createdByProfile = computed(() =>
      environment.value ? userStore.getProfile(environment.value.created_by) : undefined
    );
    const publishedByProfile = computed(() =>
      environment.value ? userStore.getProfile(environment.value.published_by) : undefined
    );

    const vagrantCloudUrl = computed(() =>
      environment.value ? `https://app.vagrantup.com/${environment.value.vagrantbox}` : '#'
    );

    function openInGitea() {
      if (environment.value?.file) {
        window.open(environment.value.file, '_blank');
      }
    }

    onMounted(async () => {
      await environmentStore.loadEnvironmentByName(props.name);
      if (!environment.value) return;

      // Load user profiles
      if (environment.value.created_by) {
        await userStore.fetchProfile(environment.value.created_by);
      }
      if (environment.value.published_by) {
        await userStore.fetchProfile(environment.value.published_by);
      }

      // Fetch experiments that use this environment
      await experimentStore.fetchExperimentsAdvanced(
        20, 0, 'published_at', true, undefined,
        { environment_mc: [props.name] }
      );
      relatedExperiments.value = experimentStore.getRows();
    });

    return {
      environment,
      relatedExperiments,
      createdByProfile,
      publishedByProfile,
      vagrantCloudUrl,
      openInGitea,
    };
  },
});
</script>
