<template>
  <div>
    <ExperimentTable :scenario="uuid" />
  </div>
</template>


<script lang="ts">
import ExperimentTable from 'components/ExperimentTable.vue';


export default {
  name: 'ExperimentList',
  components: {ExperimentTable,},

  props: {
    uuid: {
      type: String,
      required: true
    }
  },

}

</script>

