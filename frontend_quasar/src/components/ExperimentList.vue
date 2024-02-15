<template>
  <div>
    <ExperimentTable2 :scenario="scenario"/>
  </div>
</template>


<script lang="ts">
import ExperimentTable2 from 'components/ExperimentTable2.vue';


export default {
  name: 'ExperimentList',
  components: {ExperimentTable2,},

  props: {
    scenario: {
      type: String,
      required: false,
    },
  }

}

</script>
