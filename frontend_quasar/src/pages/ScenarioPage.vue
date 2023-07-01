<template>
  <q-page class="row items-center justify-evenly">
    <ScenarioList></ScenarioList>
  </q-page>
</template>

<script lang="ts">
import ScenarioList from 'components/ScenarioList.vue';

export default {
  name: 'IndexPage',

  components: {
    ScenarioList
  },

};

</script>
