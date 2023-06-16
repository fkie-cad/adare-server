<template>
  <q-page class="row items-center justify-evenly">
    <LoginForm></LoginForm>
  </q-page>
</template>


<script lang="ts">
import LoginForm from 'components/LoginForm.vue';

export default {
  name: 'LoginPage',

  components: {
    LoginForm
  },

};
</script>
