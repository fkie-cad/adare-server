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
    >
      <template v-slot:option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section>
            <q-item-label>
              <q-icon name="check" v-if="scope.selected" size="1rem"/>
              <q-icon v-else size="1rem"/>
              {{ scope.opt }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-select>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import { Filter, FilterEntry } from 'src/datatypes/advancedtable';

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
      // create filter entry for each selected field
      for (const selectedField of selectedFields.value) {
        const filterEntry: FilterEntry = {
          field: props.filter.api_field,
          type: 'select',
          value: selectedField,
        };
        emit('update-selectFilter', filterEntry);
      }
    };

    return {
      selectedFields,
      ChangeSelectFilter,
      visible,
    }

  },
});


</script>
