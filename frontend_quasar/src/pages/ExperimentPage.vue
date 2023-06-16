<template>
  <q-page class="row items-center justify-evenly tw-overflow-visible">
    <div v-if="showExperimentNotFound">

    </div>
    <div v-else>
      {{ uuid }}
    </div>
  </q-page>
</template>

<script lang="ts">
import { useLoginStore } from 'stores/login';
import {onMounted, ref, toRefs} from 'vue';

export default {
  name: 'ExperimentPage',

  props: {
    uuid: {
      type: String,
      default: ''
    },
  },

  setup(props){
    const { uuid } = toRefs(props)
    const showExperimentNotFound = ref(true)

    const LoginStore = useLoginStore()

    onMounted( () => {
      if (uuid.value == '') {
        showExperimentNotFound.value = true
      } else {
        showExperimentNotFound.value = false
      }
    })

    return {
      LoginStore,
      showExperimentNotFound,
    }

  }
}
</script>

