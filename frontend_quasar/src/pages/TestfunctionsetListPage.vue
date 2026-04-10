<template>
  <q-page>
    <div class="row no-wrap">
      <FilterSidebar
        v-model="sidebarOpen"
        :tags-by-scope="tagsByScope"
        :selected-tags="selectedTags"
        @update:selected-tags="onTagsChanged"
      />
      <div class="col q-pa-lg">
        <div class="row items-center q-mb-sm">
          <q-btn
            flat dense round
            icon="filter_list"
            @click="sidebarOpen = !sidebarOpen"
            class="q-mr-sm"
          >
            <q-tooltip>Toggle filters</q-tooltip>
          </q-btn>
        </div>
        <ActiveFilters
          :selected-tags="selectedTags"
          @remove="removeTag"
          @clear="clearTags"
        />
        <TestfunctionSetList />
      </div>
    </div>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import TestfunctionSetList from 'components/TestfunctionSetList.vue';
import FilterSidebar, { TagsByScope } from 'src/components/FilterSidebar.vue';
import ActiveFilters from 'src/components/ActiveFilters.vue';
import { useTestfunctionSetStore } from 'src/store/testfunctionset';

export default defineComponent({
  name: 'TestfunctionsetListPage',
  components: { TestfunctionSetList, FilterSidebar, ActiveFilters },
  setup() {
    const testfunctionSetStore = useTestfunctionSetStore();
    const sidebarOpen = ref(true);
    const tagsByScope = ref<TagsByScope>({});
    const selectedTags = ref<string[]>([]);

    async function loadFilterOptions() {
      try {
        const opts = await testfunctionSetStore.fetchFilterOptions('');
        if (opts.tags_by_scope) {
          tagsByScope.value = opts.tags_by_scope;
        }
      } catch (e) {
        // Filter options not available
      }
    }

    function onTagsChanged(tags: string[]) {
      selectedTags.value = tags;
      refetchWithFilters();
    }

    function removeTag(tag: string) {
      selectedTags.value = selectedTags.value.filter(t => t !== tag);
      refetchWithFilters();
    }

    function clearTags() {
      selectedTags.value = [];
      refetchWithFilters();
    }

    async function refetchWithFilters() {
      const scopedFilters = selectedTags.value.length > 0
        ? { tags_scoped: selectedTags.value }
        : undefined;
      await testfunctionSetStore.fetchTestfunctionSetsAdvanced(8, 0, undefined, false, undefined, scopedFilters);
    }

    onMounted(async () => {
      await loadFilterOptions();
    });

    return {
      sidebarOpen,
      tagsByScope,
      selectedTags,
      onTagsChanged,
      removeTag,
      clearTags,
    };
  },
});
</script>
