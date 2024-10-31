<template>
  <q-card
    square
    flat
    class=""
  >
    <div v-show="!LoginStore.IsLoggedIn">
      <q-card-section>
        <h3 class="text-h3 q-ma-none q-mb-xl text-center">Sign In</h3>
        <div class="flex justify-center">
          <q-icon name="o_account_circle" size="10em"></q-icon>
        </div>
      </q-card-section>
      <q-card-section>
        <q-banner
          class="bg-red-10 text-center text-white"
          rounded
          v-show="errorShown"
        >
          <template v-slot:avatar>
            <q-icon name="error" />
          </template>
          <div class="text-h5">{{ errorMessage }}</div>
        </q-banner>
      </q-card-section>
      <q-card-actions class="q-px-lg">
        <q-btn unelevated size="lg" color="blue-grey-9" class="full-width" @click="login" label="Sign In with Gitea" />
      </q-card-actions>
    </div>
  </q-card>
</template>

<script lang="ts">
import {ref, reactive, onMounted} from 'vue';
import { useLoginStore } from 'src/store/login';
import { useLoggedInUserStore } from 'src/store/loggedinuser';
import { storeToRefs } from 'pinia'
import { api } from 'src/boot/axios';
import { FRONTEND_URL } from 'src/boot/axios';
import {useRouter} from 'vue-router';

export default {
  'name': 'LoginForm',

  setup() {

    let login_data = reactive({
      username: '',
      password: '',
    })
    let errorMessage = ref('')
    let errorShown = ref(false)
    let directly_logged_in = ref(false)

    const router = useRouter()

    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)

    const LoginStore = useLoginStore()
    storeToRefs(LoginStore)

    const login = async () => {
      // create state for preventing csrf attacks (https://auth0.com/docs/protocols/state-parameters)
      const state = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)

      const resp = await api.get('auth/gitea/callback/' + `?redirect_uri=${FRONTEND_URL}login/oauth&state=${state}`)
      if (resp.status === 200) {
        // save the state in the local storage
        localStorage.setItem('state', state)

        // open the redirect url in a new tab
        console.log(resp.data.url)
        window.open(resp.data.url, '_blank')

      } else {
        setErrorMessage('Something went wrong. Please try again later.')
        showErrorMessage()
      }

    }

    async function logout () {
      LoginStore.Logout()
      LoggedInUserStore.ResetUser()
      await router.push('/login')
      await LoggedInUserStore.UpdateProfileInformation()
    }

    function setErrorMessage(message: string){
      errorMessage.value = message
    }
    function showErrorMessage(){
      errorShown.value = true
    }
    function hideErrorMessage(){
      errorShown.value = false
    }
    function reset () {
      login_data.username = ''
      login_data.password = ''
    }

    onMounted(async () => {
      if(LoginStore.IsLoggedIn){
        await router.push('/profile')
      }
    })

    return {
      login_data,
      errorMessage,
      errorShown,
      directly_logged_in,
      LoginStore,
      login,
      logout,
      reset,
      hideErrorMessage,
    }
  }
}
</script>
