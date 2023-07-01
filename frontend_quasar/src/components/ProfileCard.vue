<template>
  <q-card
      class="col-3"
    >
      <q-card-section
        class="column justify-center items-center bg-teal-2 tw-h-32"
      >
        <ProfileImage
          offset_classes="tw-top-8"
          :editable="true"
          :username="username"
          size="lg"
        />
      </q-card-section>
      <q-card-section>
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            username
          </div>
          <div class="column text-h6">
            {{ username }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between  q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            email
          </div>
          <div class="column text-h6">
            {{ UserStore.GetUserEmail(username) }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between  q-pa-sm">
          <div class="column text-h6 tw-text-gray-600">
            roles
          </div>
          <div class="column">
            <span v-for="role in UserStore.GetUserGroups(username)" v-bind:key="role.id" class="tw-rounded q-pa-xs" :class="role_color_mapping[role]">
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
            :src="achiev.image"
            style="height: 110px; width: 110px"
            v-for="achiev in UserStore.GetUserAchievements(username).values()"
            v-bind:key="achiev.id"
          >
            <q-tooltip>
              {{ achiev.description }}
            </q-tooltip>
          </q-img>
        </div>
      </q-card-section>
    </q-card>
</template>

<script lang="ts">
import { useUserStore } from 'stores/user';
import { useLoginStore} from 'stores/login';
import { useLoggedInUserStore } from 'stores/loggedinuser';
import ProfileImage from 'components/ProfileImage.vue';
import {onMounted, ref} from 'vue';
import {storeToRefs} from 'pinia';
import { useRouter } from 'vue-router';

export default {
  name: 'ProfileCard',
  components: {
    ProfileImage
  },
  props: ['username'],

  setup(props){

    const LoginStore = useLoginStore()
    storeToRefs(LoginStore)

    const UserStore = useUserStore()
    storeToRefs(UserStore)

    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)

    let role_color_mapping = ref({
      'admin': 'bg-red-5',
      'supervisor': 'bg-amber-5',
    })

    onMounted(async () => {
      await UserStore.UpdateProfileInformation(props.username)
    })


    return {
      UserStore,
      role_color_mapping,
    }

  }
}
</script>
