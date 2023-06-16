<template>
  <q-card
      class="col-3"
    >
      <q-card-section
        class="column justify-center items-center bg-teal-2 tw-h-32"
      >
        <ProfileImage
          editable
          offset_classes="tw-top-12"
        />
      </q-card-section>
      <q-card-section>
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            username
          </div>
          <div class="column text-h6">
            {{ UserStore.GetUserUsername }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between  q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            email
          </div>
          <div class="column text-h6">
            {{ UserStore.GetUserUsername }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between  q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            roles
          </div>
          <div class="column">
            <span v-for="role in UserStore.GetUserGroups" v-bind:key="role.id" class="tw-rounded q-pa-xs" :class="role_color_mapping[role]">
              {{ role }}
            </span>
          </div>
        </div>
        <q-separator />
        <div class="row justify-between  q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            achievements
          </div>
        </div>
        <div class="row justify-evenly">
          <q-img
            :src="achievements.image"
            style="height: 110px; width: 110px"
            v-for="achievements in UserStore.GetUserAchievements.values()"
            v-bind:key="achievements.id"
          >
            <q-tooltip>
              {{ achievements.description }}
            </q-tooltip>
          </q-img>
        </div>
      </q-card-section>
    </q-card>
</template>

<script lang="ts">
import { useUserStore } from 'stores/user';
import { useLoginStore} from 'stores/login';
import ProfileImage from 'components/ProfileImage.vue';
import {onMounted, ref} from 'vue';
import {storeToRefs} from 'pinia';
import { useRouter } from 'vue-router';

export default {
  name: 'ProfileCard',
  components: {
    ProfileImage
  },

  setup(){
    const LoginStore = useLoginStore()
    storeToRefs(LoginStore)

    const UserStore = useUserStore()
    storeToRefs(UserStore)

    const router = useRouter()

    let role_color_mapping = ref({
      'admin': 'bg-red-5',
      'supervisor': 'bg-amber-5',
    })

    onMounted(async () => {
      if (!LoginStore.IsLoggedIn){
        await router.push('/login')
      }else{
        await UserStore.UpdateProfileInformation()
      }
    })

    return {
      UserStore,
      role_color_mapping,
    }

  }
}
</script>
