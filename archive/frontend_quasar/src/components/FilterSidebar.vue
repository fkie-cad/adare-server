<template>
  <q-drawer
    v-model="drawerOpen"
    side="left"
    :width="240"
    bordered
    :breakpoint="700"
    class="filter-sidebar"
  >
    <q-scroll-area class="fit">
      <div class="q-pa-md">
        <div class="row items-center justify-between q-mb-sm">
          <span class="text-subtitle1 text-weight-bold">Filters</span>
          <q-btn flat dense round icon="close" size="sm" @click="drawerOpen = false" />
        </div>

        <q-input
          v-model="tagSearch"
          dense
          outlined
          placeholder="Filter tags..."
          class="q-mb-md"
          clearable
        >
          <template #prepend>
            <q-icon name="search" size="xs" />
          </template>
        </q-input>

        <!-- Tag scope sections -->
        <q-expansion-item
          v-for="(tags, scope) in filteredTagsByScope"
          :key="scope"
          :label="scope === 'unscoped' ? 'Other Tags' : String(scope)"
          :header-class="'text-uppercase text-caption text-weight-bold'"
          dense
          default-opened
        >
          <div class="q-pl-md q-pr-sm">
            <q-checkbox
              v-for="tag in tags"
              :key="tag.name"
              :model-value="isTagSelected(tag.name)"
              @update:model-value="toggleTag(tag.name)"
              :label="`${tag.value} (${tag.count})`"
              dense
              class="full-width q-mb-xs"
              size="sm"
            />
          </div>
        </q-expansion-item>

        <!-- Entity-specific filter sections -->
        <slot name="extra-filters" />
      </div>
    </q-scroll-area>
  </q-drawer>
</template>

<script lang="ts">
import { defineComponent, ref, computed, PropType, watch } from 'vue';

export interface TagOption {
  value: string;
  name: string;
  count: number;
}

export interface TagsByScope {
  [scope: string]: TagOption[];
}

export default defineComponent({
  name: 'FilterSidebar',
  props: {
    modelValue: {
      type: Boolean,
      default: true,
    },
    tagsByScope: {
      type: Object as PropType<TagsByScope>,
      default: () => ({}),
    },
    selectedTags: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
  },
  emits: ['update:modelValue', 'update:selectedTags'],
  setup(props, { emit }) {
    const drawerOpen = computed({
      get: () => props.modelValue,
      set: (val) => emit('update:modelValue', val),
    });

    const tagSearch = ref('');

    const filteredTagsByScope = computed(() => {
      const result: TagsByScope = {};
      for (const [scope, tags] of Object.entries(props.tagsByScope)) {
        const filtered = tags.filter((tag) =>
          !tagSearch.value || tag.value.toLowerCase().includes(tagSearch.value.toLowerCase())
        );
        if (filtered.length > 0) {
          result[scope] = filtered;
        }
      }
      return result;
    });

    function isTagSelected(tagName: string): boolean {
      return props.selectedTags.includes(tagName);
    }

    function toggleTag(tagName: string) {
      const newTags = isTagSelected(tagName)
        ? props.selectedTags.filter((t) => t !== tagName)
        : [...props.selectedTags, tagName];
      emit('update:selectedTags', newTags);
    }

    return {
      drawerOpen,
      tagSearch,
      filteredTagsByScope,
      isTagSelected,
      toggleTag,
    };
  },
});
</script>
