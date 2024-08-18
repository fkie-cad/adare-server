<template>
  <q-page class="row items-center justify-evenly">
    <div class="row q-pa-none fit items-center justify-evenly">
      <div class="col-6 q-pa-xl shadow-24">
        <WelcomeCard/>
      </div>
    </div>
  </q-page>
</template>


<script lang="ts">
import WelcomeCard from 'components/WelcomeCard.vue';

export default {
  name: 'HomePage',

  components: {
    WelcomeCard,
  },

};
</script>
