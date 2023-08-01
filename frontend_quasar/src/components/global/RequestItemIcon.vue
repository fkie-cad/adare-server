<template>
  <q-icon
    :name="icon"
    :color="color"
    :size="size"
  >
    <q-tooltip v-if="tooltip">
      {{ item }}
    </q-tooltip>
  </q-icon>

</template>

<script lang="ts">
import { request_obj_icon_mapping } from 'src/constants/mappings';
import {computed} from 'vue';

export default {
  name: 'RequestItemIcon',
  props: {
    item: {
      type: String,
      required: true,
    },
    size: {
      type: String,
      default: '2.5em',
    },
    color: {
      type: String,
      default: 'black',
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
  },

  setup(props){

    function GetIcon(){
      return request_obj_icon_mapping[props.item.toLowerCase() as keyof typeof request_obj_icon_mapping]
    }

    const icon = computed(GetIcon)

    return {
      icon,
    }
  }
}

</script>
