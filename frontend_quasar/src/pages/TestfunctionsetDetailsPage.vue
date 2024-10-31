<template>
  <q-page class="flex justify-center">
    <TestfunctionSetDetail :name="name" />
  </q-page>
</template>

<script lang="ts">
import TestfunctionSetDetail from 'components/TestfunctionSetDetail.vue';

export default {
  name: 'TestfunctionsetDetailsPage',

  components: {
    TestfunctionSetDetail

  },

  props: {
    name: {
      type: String,
      required: true,
    },
  },

};

</script>


