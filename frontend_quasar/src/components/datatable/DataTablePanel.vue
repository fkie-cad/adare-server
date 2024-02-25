<template>
  <div class="col">
    <div class="row">
      <q-btn
        flat dense
        :icon="tableProps.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
        @click="tableProps.toggleFullscreen"
      />
      <q-btn
        icon="settings"
        color="primary"
      >
        <q-menu
          anchor="bottom right"
          self="top right"
        >
          <q-list
            dense
          >
            <q-item>
              <q-checkbox
                v-model="show_all_columns"
                label="show all"
                @update:model-value="ShowAllColumns()"
              />
              <q-checkbox
                v-model="hide_all_columns"
                label="hide all"
                @update:model-value="HideAllColumns()"
              />
            </q-item>
            <q-separator />
            <q-item
              v-for="col in hideable_columns"
              :key="col.field"
            >
              <q-checkbox v-model="visible_columns" :val=col.field :label="col.label" @update:model-value="AdjustShowHideAllColumns()"/>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </div>
  </div>
</template>

<script lang="ts">
import { ref } from 'vue';

export default {
  name: 'DataTablePanel',
  props: {
    tableProps: {
      type: Object,
      required: true,
    },
    visibleColumns: {
      type: Array,
      required: true,
    },
    columns: {
      type: Array,
      required: true,
    },

  },


  setup(props) {

    const show_all_columns = ref(false);
    const hide_all_columns = ref(false);
    const visible_columns = ref([]);
    const hideable_columns = ref([]);

    // determine hideable columns by attribute "hideable" in column definition
    for (let col of props.columns) {
      if (col.hideable) {
        hideable_columns.value.push(col);
      }
    }

    return {
    };
  },
};
</script>
