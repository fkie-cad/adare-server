<template>
  <div>
    <ExperimentTable :scenario="scenario"/>
  </div>
</template>


<script lang="ts">
import ExperimentTable from 'components/ExperimentTable.vue';


export default {
  name: 'ExperimentList',
  components: {ExperimentTable,},

  props: {
    scenario: {
      type: String,
      required: false,
    },
  }

}

</script>
