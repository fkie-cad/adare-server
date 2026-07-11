<template>
  <q-input
    outlined
    dense
    v-model="search_filter"
    @update:model-value="ChangeSearchFilter()"
    label="search"
    style="width: 200px"
  >
    <template v-slot:append>
      <q-icon name="search" />
    </template>
  </q-input>
</template>
<script lang="ts">
import { FilterEntry } from 'src/models/advancedtable';
import {ref} from 'vue';

export default {
  name: 'DataTableSearchFilter',
  emits: ['update-searchFilter'],

  setup(props, {emit}) {
    const search_filter = ref('');
    const ChangeSearchFilter = () => {
      const filterEntry: FilterEntry = {
        field: 'search',
        type: 'search',
        value: search_filter.value,
      };
      emit('update-searchFilter', filterEntry);
    };

    return {
      search_filter,
      ChangeSearchFilter,
    };
  },
};

</script>
