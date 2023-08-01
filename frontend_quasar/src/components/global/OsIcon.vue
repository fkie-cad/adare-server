<template>
  <q-icon
    :name="icon"
    :size="size"
    :color="icon_color"
  >
    <q-tooltip v-if="tooltip">
      {{ item }}
    </q-tooltip>
  </q-icon>

</template>

<script lang="ts">
import { os_icon_mapping, os_color_mapping } from 'src/constants/mappings';
import {computed, ref} from 'vue';


export default {
  name: 'OsIcon',
  props: {
    item: {
      type: String,
      required: true,
    },
    size: {
      type: String,
      default: '2em',
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
  },

  setup(props){

    function GetIcon(){
      return os_icon_mapping[props.item.toLowerCase() as keyof typeof os_icon_mapping]
    }

    function GetIconColor(){
      return os_color_mapping[props.item.toLowerCase() as keyof typeof os_color_mapping]
    }

    const icon = computed(GetIcon)
    const icon_color = computed(GetIconColor)

    return {
      icon,
      icon_color,
    }
  }
}

</script>
