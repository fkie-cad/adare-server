<template>
  <q-page>
    <RequestOverview
      :uuid="uuid"
    />
  </q-page>
</template>

<script lang="ts">
import RequestOverview from 'components/RequestOverview.vue';

export default {
  name: 'RequestsPage',
  components: {
    RequestOverview,
  },
  props: {
    uuid: {
      type: String,
      required: true,
    },
  },

};

</script>
