<template>
  <q-page class="row items-center justify-evenly">
    <div class="row q-pa-none fit items-center justify-evenly">
      <OauthRedirect />
    </div>
  </q-page>
</template>


<script lang="ts">
import OauthRedirect from 'components/OauthRedirect.vue';

export default {
  name: 'OatuhWaitingPage',

  components: {
    OauthRedirect,
  },

};
</script>
