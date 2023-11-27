from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, Request, Response
from .models import Pet
from .serializer import PetSerializer
from traits.models import Trait
from groups.models import Group
from rest_framework.pagination import PageNumberPagination


class PetsView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pet_traits = request.query_params.get("trait", None)
        if pet_traits:
            pet = Pet.objects.filter(traits__name = pet_traits)
        else:
            pet = Pet.objects.all()
        
        result_page = self.paginate_queryset(pet, request, view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        pet_data = request.data
        serializer = PetSerializer(data=pet_data)
        serializer.is_valid(raise_exception=True)

        traits_data = serializer.validated_data.pop("traits")
        group_data = serializer.validated_data.pop("group")

        group_name = group_data["scientific_name"]
        try:
            group = Group.objects.get(scientific_name=group_name)
        except Group.DoesNotExist:
            group = Group.objects.create(**group_data)

        pet = Pet.objects.create(**serializer.validated_data, group=group)

        traits = []
        for trait_data in traits_data:
            trait_name = trait_data["name"].lower()
            try:
                trait = Trait.objects.get(name__iexact=trait_name)
            except Trait.DoesNotExist:
                trait = Trait.objects.create(name=trait_name)
            traits.append(trait)
        pet.traits.set(traits)

        serializer = PetSerializer(pet)
        return Response(serializer.data, 201)


class PetsDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet,id=pet_id)
        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet,id=pet_id)
        pet.delete()
        return Response(status=204)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet,id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if "group" in request.data:
            group_data = serializer.validated_data.pop("group")
            group_name = group_data["scientific_name"]
            try:
                group = Group.objects.get(scientific_name=group_name)
            except Group.DoesNotExist:
                group = Group.objects.create(**group_data)
            setattr(pet, "group", group)
        else:
            setattr(pet, "group", pet.group)

        if "traits" in request.data:
            traits_data = serializer.validated_data.pop("traits")
            traits = []
            for trait_data in traits_data:
                try:
                    trait = Trait.objects.get(name__iexact=trait_data["name"])
                    traits.append(trait)
                except Trait.DoesNotExist:
                    trait = Trait.objects.create(**trait_data)
                    traits.append(trait)
            pet.traits.set(traits)
        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()
        serializer = PetSerializer(pet)
        return Response(serializer.data, 200)

