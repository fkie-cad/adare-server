<template>
  <div v-if="selectedTags.length > 0" class="row items-center q-gutter-xs q-mb-sm">
    <span class="text-caption text-grey-7">Active:</span>
    <q-chip
      v-for="tag in selectedTags"
      :key="tag"
      :color="getChipColor(tag)"
      text-color="white"
      removable
      dense
      size="sm"
      @remove="$emit('remove', tag)"
    >
      {{ tag }}
    </q-chip>
    <q-btn flat dense no-caps size="sm" color="primary" label="Clear all" @click="$emit('clear')" />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { getTagColor } from 'src/constants/tagColors';

export default defineComponent({
  name: 'ActiveFilters',
  props: {
    selectedTags: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
  },
  emits: ['remove', 'clear'],
  setup() {
    function getChipColor(tagName: string): string {
      const parts = tagName.split(':');
      if (parts.length === 2) {
        return getTagColor(parts[0]);
      }
      return getTagColor(null);
    }

    return { getChipColor };
  },
});
</script>
