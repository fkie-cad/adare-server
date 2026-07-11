<template>
  <q-page class="q-pa-lg">
    <!-- Stats Cards -->
    <div class="row q-col-gutter-md q-mb-lg">
      <div class="col-3" v-for="stat in statCards" :key="stat.label">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-overline text-grey-7">{{ stat.label }}</div>
            <div class="text-h4 text-weight-bold">{{ stat.value }}</div>
            <div v-if="stat.subtitle" class="text-caption text-grey-6">{{ stat.subtitle }}</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Quick Search -->
    <q-card flat bordered class="q-mb-lg">
      <q-card-section>
        <q-input
          v-model="searchQuery"
          outlined
          dense
          placeholder="Search experiments, environments, test functions..."
          @keyup.enter="doSearch"
        >
          <template #prepend>
            <q-icon name="search" />
          </template>
          <template #append>
            <q-btn-toggle
              v-model="searchTarget"
              flat
              dense
              toggle-color="primary"
              :options="[
                { label: 'Experiments', value: 'experiment' },
                { label: 'Environments', value: 'environment' },
                { label: 'Test Sets', value: 'testfunctionset' },
              ]"
              size="sm"
            />
          </template>
        </q-input>
      </q-card-section>
    </q-card>

    <!-- Recent Items -->
    <div class="row q-col-gutter-md q-mb-lg">
      <!-- Recent Experiments -->
      <div class="col-6">
        <q-card flat bordered>
          <q-card-section class="row items-center justify-between">
            <span class="text-subtitle1 text-weight-bold">Recent Experiments</span>
            <q-btn flat dense no-caps color="primary" label="View all →" to="/experiment" />
          </q-card-section>
          <q-separator />
          <q-list>
            <q-item
              v-for="exp in recentExperiments"
              :key="exp.ulid"
              clickable
              :to="`/experiment/${exp.name}`"
            >
              <q-item-section>
                <q-item-label class="text-weight-medium text-primary">{{ exp.name }}</q-item-label>
                <q-item-label caption>by {{ exp.published_by }} · {{ formatDate(exp.published_at) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="row q-gutter-xs">
                  <ScopedTagBadge v-for="tag in exp.tags.slice(0, 2)" :key="tag.name" :tag="tag" />
                </div>
              </q-item-section>
            </q-item>
            <q-item v-if="recentExperiments.length === 0">
              <q-item-section>
                <q-item-label caption>No experiments yet</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <!-- Recent Environments -->
      <div class="col-6">
        <q-card flat bordered>
          <q-card-section class="row items-center justify-between">
            <span class="text-subtitle1 text-weight-bold">Recent Environments</span>
            <q-btn flat dense no-caps color="primary" label="View all →" to="/environment" />
          </q-card-section>
          <q-separator />
          <q-list>
            <q-item
              v-for="env in recentEnvironments"
              :key="env.ulid"
              clickable
              :to="`/environment/${env.name}`"
            >
              <q-item-section>
                <q-item-label class="text-weight-medium text-primary">{{ env.name }}</q-item-label>
                <q-item-label caption>{{ env.os_info?.distribution }} {{ env.os_info?.version }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="row q-gutter-xs">
                  <ScopedTagBadge v-for="tag in env.tags.slice(0, 2)" :key="tag.name" :tag="tag" />
                </div>
              </q-item-section>
            </q-item>
            <q-item v-if="recentEnvironments.length === 0">
              <q-item-section>
                <q-item-label caption>No environments yet</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>

    <!-- Popular Tags -->
    <q-card flat bordered v-if="popularTags.length > 0">
      <q-card-section>
        <div class="text-subtitle1 text-weight-bold q-mb-sm">Popular Tags</div>
        <div class="row q-gutter-sm">
          <q-chip
            v-for="tag in popularTags"
            :key="tag.name"
            :color="getTagColor(tag.scope)"
            text-color="white"
            clickable
            @click="navigateToTag(tag)"
            size="sm"
          >
            {{ tag.name }}
            <q-badge color="white" text-color="dark" floating>{{ tag.count }}</q-badge>
          </q-chip>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStatsStore } from 'src/store/stats';
import { useExperimentStore } from 'src/store/experiment';
import { useEnvironmentStore } from 'src/store/environment';
import { getTagColor } from 'src/constants/tagColors';
import ScopedTagBadge from 'src/components/global/ScopedTagBadge.vue';
import { Experiment, Environment } from 'src/models/experiment';

interface PopularTag {
  name: string;
  value: string;
  scope: string | null;
  count: number;
}

export default defineComponent({
  name: 'HomePage',
  components: { ScopedTagBadge },
  setup() {
    const router = useRouter();
    const statsStore = useStatsStore();
    const experimentStore = useExperimentStore();
    const environmentStore = useEnvironmentStore();

    const searchQuery = ref('');
    const searchTarget = ref('experiment');
    const recentExperiments = ref<Experiment[]>([]);
    const recentEnvironments = ref<Environment[]>([]);
    const popularTags = ref<PopularTag[]>([]);

    const statCards = computed(() => [
      { label: 'Experiments', value: statsStore.stats.experiment_count || 0 },
      { label: 'Environments', value: statsStore.stats.environment_count || 0 },
      { label: 'Test Function Sets', value: statsStore.stats.testfunctionset_count || 0 },
      { label: 'Runs', value: statsStore.stats.run_count || 0 },
    ]);

    function formatDate(dateStr: string) {
      if (!dateStr) return '';
      const d = new Date(dateStr);
      const now = new Date();
      const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
      if (diff === 0) return 'today';
      if (diff === 1) return 'yesterday';
      if (diff < 7) return `${diff} days ago`;
      return d.toLocaleDateString();
    }

    function doSearch() {
      if (!searchQuery.value) return;
      router.push({ path: `/${searchTarget.value}`, query: { search: searchQuery.value } });
    }

    function navigateToTag(tag: PopularTag) {
      router.push({ path: '/experiment', query: { tags_scoped: tag.name } });
    }

    onMounted(async () => {
      await statsStore.fetchStats();

      // Fetch recent experiments
      await experimentStore.fetchExperimentsAdvanced(5, 0, 'published_at', true);
      recentExperiments.value = experimentStore.getRows();

      // Fetch recent environments
      await environmentStore.fetchEnvironmentsAdvanced(5, 0, 'published_at', true);
      recentEnvironments.value = environmentStore.getRows();

      // Fetch popular tags from filter options
      try {
        const filterOpts = await experimentStore.fetchFilterOptions('');
        if (filterOpts.tags_by_scope) {
          const allTags: PopularTag[] = [];
          for (const [scope, tags] of Object.entries(filterOpts.tags_by_scope)) {
            for (const tag of tags as PopularTag[]) {
              allTags.push({
                name: tag.name,
                value: tag.value,
                scope: scope === 'unscoped' ? null : scope,
                count: tag.count,
              });
            }
          }
          // Sort by count descending, take top 12
          popularTags.value = allTags.sort((a, b) => b.count - a.count).slice(0, 12);
        }
      } catch (e) {
        // Filter options not available yet, skip
      }
    });

    return {
      searchQuery,
      searchTarget,
      statCards,
      recentExperiments,
      recentEnvironments,
      popularTags,
      formatDate,
      doSearch,
      navigateToTag,
      getTagColor,
    };
  },
});
</script>
