<template>
    <div class="tw-overflow-visible tw-relative" :class="offset_classes">
      <q-avatar
        color="secondary"
        size="100px"
        text-color="white"
      >
        <div v-if="avatar_thumbnail != ''">
            <img v-bind:src="avatar_thumbnail" alt="" class="object-cover">
        </div>
        <div v-else>
          {{ UserStore.GetUserUsername.charAt(0).toUpperCase() }}
        </div>
      </q-avatar>
      <div>
        <q-btn
            icon="edit"
            round
            v-if="editable"
            size="1em"
            color="primary"
            style="right: -4em; top: -2em; z-index: 1"
            @click="show_dialog = true"
        />
      </div>
    </div>
    <q-dialog v-model="show_dialog">
        <q-card>
          <q-card-section class="row items-center">
            <div class="text-h6">Profile Image</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup />
          </q-card-section>

          <q-separator />

          <q-card-section >
            <div class="text-subtitle1 q-mb-md">
              If you are uploading a profile image you and other users will be able to see it.
            </div>
            <div class="row justify-center q-my-md">
              <div class="tw-overflow-visible tw-relative">
                <q-avatar
                  color="secondary"
                  size="100px"
                  text-color="white"
                >
                  <div v-if="avatar_thumbnail != ''">
                      <img v-bind:src="avatar_thumbnail" alt="" class="object-cover">
                  </div>
                  <div v-else>
                    {{ UserStore.GetUserUsername.charAt(0).toUpperCase() }}
                  </div>
                </q-avatar>
                <div>
                  <q-btn
                      icon="delete"
                      round
                      size="1em"
                      color="accent"
                      style="right: -4em; top: -2em; z-index: 1"
                      @click="remove_profile_image"
                  />
                </div>
              </div>
            </div>
            <div class="row justify-center q-my-md">
              <q-file
                v-model="file"
                label="Change profile image"
                outlined
                style="max-width: 300px"
              >
                <template v-slot:append>
                  <q-icon name="image" />
                </template>
              </q-file>
              <q-btn
                label="Upload"
                color="primary"
                @click="upload_profile_image"
                class="q-mx-md"
              />
            </div>
          </q-card-section>

        </q-card>
      </q-dialog>
</template>

<script lang="ts">
import { useLoginStore } from 'stores/login';
import { useUserStore } from 'stores/user';
import API_URLS from 'src/api'
import axios from 'axios';
import {onMounted, ref, toRefs } from 'vue';
import { storeToRefs } from 'pinia'


export default {
  name: 'ProfileImage',

  props: {
    editable: {
      type: Boolean,
      default: false
    },
    offset_classes: {
      type: String,
      default: ''
    }
  },

  setup(props) {
    const show_dialog = ref(false)
    const LoginStore = useLoginStore()
    const UserStore = useUserStore()
    const { avatar_thumbnail } = storeToRefs(UserStore)
    const file = ref<File | null>(null)

    async function upload_profile_image() {
      if (file.value != null) {
        let formData = new FormData();
        formData.append('avatar', file.value as File);
        await axios.put(
          API_URLS.USER_API + 'profile/avatar/',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        await UserStore.UpdateProfileInformation()
      }
    }

    async function remove_profile_image(){
      await axios.delete(
        API_URLS.USER_API + 'profile/avatar/',
      )
      UserStore.RemoveUserAvatarThumbnail()
      await UserStore.UpdateProfileInformation()
    }

    return {
      LoginStore,
      UserStore,
      file,
      avatar_thumbnail,
      upload_profile_image,
      remove_profile_image,
      show_dialog,
    }

  }
}
</script>
