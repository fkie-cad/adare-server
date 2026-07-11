<template>
    <q-select
      outlined
      dense
      options-dense
      use-input
      input-debounce="0"
      v-model="selectedFields"
      :label="filter.name"
      :options="filter.options"
      multiple
      display-value=""
      @update:model-value="ChangeSelectFilter"
      @clear="ChangeSelectFilter"
      style="width: 200px"
      class="q-pr-md"
      v-show="visible"
      :color="filter.color || 'primary'"
    >
      <template v-slot:option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section>
            <q-item-label>
              <q-icon name="check" v-if="scope.selected" size="1rem"/>
              <q-icon v-else size="1rem"/>
              {{ displayLabel(scope.opt) }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-select>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import { Filter, FilterEntry } from 'src/models/advancedtable';

export default defineComponent({
  name: 'DataTableSelectFilter',
  emits: ['update-selectFilter'],
  props: {
    filter: {
      type: Object,
      required: true,
    },
    // actual filter object (influenced by other filters)
    actualFilter: {
      type: Object as () => Filter,
      required: true,
    },
  },

  setup(props, {emit}) {
    const selectedFields = ref<string[]>([]);
    const visible = ref(true);

    onMounted(() => {
      // set selected fields to actual filter
      if (props.filter.options.length === 0) {
        visible.value = false;
      }
    });

    const ChangeSelectFilter = () => {
      const filterEntry: FilterEntry = {
        field: props.filter.api_field,
        type: 'select',
        value: selectedFields.value.join(','),
      };
      emit('update-selectFilter', filterEntry);
    };

    function displayLabel(opt: string): string {
      // Strip scope: prefix for scoped tag filters
      if (props.filter.scope && opt.includes(':')) {
        return opt.split(':').slice(1).join(':');
      }
      return opt;
    }

    return {
      selectedFields,
      ChangeSelectFilter,
      displayLabel,
      visible,
    }

  },
});


</script>
