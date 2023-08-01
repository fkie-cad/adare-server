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
          class="bg-red-10 text-center"
          rounded
          v-show="errorShown"
        >
          <template v-slot:avatar>
            <q-icon name="error" />
          </template>
          <div class="text-h5">{{ errorMessage }}</div>
        </q-banner>
      </q-card-section>
      <q-card-section>
        <q-form
          class="q-px-sm q-pt-sm"
          @submit="login"
          @reset="reset"
        >
          <q-input
            square
            clearable
            v-model="login_data.email"
            type="email"
            label="Email"
            @clear="hideErrorMessage"
            class="q-pa-sm"
          >
            <template v-slot:prepend>
              <q-icon name="email"/>
            </template>
          </q-input>
          <q-input
            square
            clearable
            v-model.lazy="login_data.password"
            type="password"
            label="Password"
            @clear="hideErrorMessage"
            class="q-pa-sm"
          >
            <template v-slot:prepend>
              <q-icon name="lock"/>
            </template>
          </q-input>
        </q-form>
      </q-card-section>
      <q-card-actions class="q-px-lg">
        <q-btn unelevated size="lg" color="blue-grey-9" class="full-width" @click="login" label="Sign In" />
      </q-card-actions>
    </div>
  </q-card>
</template>

<script lang="ts">
import {ref, reactive, onMounted} from 'vue';
import { useLoginStore } from 'stores/login';
import { useLoggedInUserStore } from 'stores/loggedinuser';
import { storeToRefs } from 'pinia'
import axios from 'axios'
import API_URLS from 'src/api'
import {useRouter} from 'vue-router';

export default {
  'name': 'LoginForm',

  setup() {

    let login_data = reactive({
      email: '',
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
      if (LoginStore.IsLoggedIn) {
        console.log('user already logged in -> log out user')
        await logout()
      }

      await axios.post(
      API_URLS.USER_API+'login/',
      {
        username: login_data.email,
        password: login_data.password
      }).then((response) => {
        // successful login
        if (response.status == 200) {
          LoginStore.SetLoginToken(
            login_data.email,
            response.data.token,
            response.data.expiry
          )
          directly_logged_in.value = true
        }
      }).catch((error) => {
        if (!error) {
          setErrorMessage('Network error')
        } else {
          if (error.response.status == 400) {
            setErrorMessage('Wrong username or password')
          } else if (error.response.status == 401) {
            setErrorMessage('Unauthorized')
          } else if (error.response.status == 500) {
            setErrorMessage('Server error')
          } else {
            setErrorMessage('Unknown error ('+error.response.status+')')
          }
        }
        showErrorMessage()
      })
      await LoggedInUserStore.UpdateProfileInformation()
      await router.push('/profile')
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
      login_data.email = ''
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
