<template>
  <q-icon
    :name="icon"
    :color="icon_color"
    :size="size"
  >
    <q-tooltip v-if="tooltip">
      {{ status }}
    </q-tooltip>
  </q-icon>

</template>

<script lang="ts">
import {status_color_mapping, status_icon_mapping } from 'src/constants/mappings';
import {computed} from 'vue';

export default {
  name: 'StatusIcon',
  props: {
    status: {
      type: String,
      required: true,
    },
    size: {
      type: String,
      default: '2.5em',
    },
    color: {
      type: String,
      default: '',
    },
    colorMapping: {
      type: Boolean,
      default: true,
    },
    tooltip: {
      type: Boolean,
      default: true,
    },
  },

  setup(props){

    function GetIconColor(){
      if (props.colorMapping){
        return status_color_mapping[props.status as keyof typeof status_color_mapping]
      } else {
        return props.color.toString()
      }
    }

    function GetIcon(){
      return status_icon_mapping[props.status as keyof typeof status_icon_mapping]
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
