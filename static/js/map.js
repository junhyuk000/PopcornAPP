// 지도 초기화
var mapContainer = document.getElementById('map');
var mapOption = {
    center: new kakao.maps.LatLng(36.5, 127.5), // 대한민국 중심 좌표
    level: 13 // 확대 수준
};
var map = new kakao.maps.Map(mapContainer, mapOption);

// 장소 검색 및 주소 변환 서비스 생성
var ps = new kakao.maps.services.Places();
var geocoder = new kakao.maps.services.Geocoder();
var markers = []; // 마커 관리 배열

// 키워드 검색 함수 (영화관 검색)
function searchCinemasAround(centerLatLng) {
    var keywords = ['롯데시네마', '메가박스', 'CGV'];
    var allResults = []; // 모든 결과 저장
    removeMarkers(); // 이전 마커 제거

    keywords.forEach(function (keyword, index) {
        ps.keywordSearch(keyword, function (data, status, pagination) {
            if (status === kakao.maps.services.Status.OK) {
                allResults = allResults.concat(data);
                console.log(`"${keyword}" 검색 성공:`, data);

                // 마지막 키워드에서 모든 결과를 표시
                if (index === keywords.length - 1 && !pagination.hasNextPage) {
                    displayResults(allResults);
                }

                // 추가 페이지 요청
                if (pagination.hasNextPage) {
                    getNextPage(pagination, allResults, index, keywords.length - 1);
                }
            } else if (status === kakao.maps.services.Status.ZERO_RESULT) {
                console.log(`"${keyword}" 검색 결과 없음`);
            } else {
                console.error(`"${keyword}" 검색 중 오류 발생`);
            }
        }, {location: centerLatLng, radius: 5000}); // 중심 좌표와 반경 5km 내 검색
    });
}

// Pagination으로 추가 페이지 가져오기
function getNextPage(pagination, allResults, currentIndex, lastIndex) {
    pagination.nextPage();
    pagination.callback = function (data, status, nextPagination) {
        if (status === kakao.maps.services.Status.OK) {
            allResults = allResults.concat(data);
            console.log('추가 페이지 검색 성공:', data);

            if (currentIndex === lastIndex && !nextPagination.hasNextPage) {
                displayResults(allResults);
            }

            if (nextPagination.hasNextPage) {
                getNextPage(nextPagination, allResults, currentIndex, lastIndex);
            }
        } else {
            console.error('추가 페이지 검색 중 오류:', status);
        }
    };
}

// 검색 결과 표시 함수
function displayResults(results) {
    var listEl = document.getElementById('placesList');
    var bounds = new kakao.maps.LatLngBounds();

    listEl.innerHTML = ''; // 기존 리스트 초기화

    results.forEach(function (result) {
        var position = new kakao.maps.LatLng(result.y, result.x);
        var marker = new kakao.maps.Marker({ position: position });
        marker.setMap(map);
        markers.push(marker);

        // 리스트 항목 생성
        var listItem = document.createElement('li');
        listItem.innerHTML = `<b>${result.place_name}</b> (${result.address_name})`;
        listItem.dataset.lat = result.y;
        listItem.dataset.lng = result.x;
        listEl.appendChild(listItem);

        // 리스트 항목 클릭 이벤트
        listItem.addEventListener('click', function () {
            map.setCenter(new kakao.maps.LatLng(this.dataset.lat, this.dataset.lng));
            map.setLevel(3); // 확대 수준 설정
        });

        bounds.extend(position); // 지도 영역 확장
    });

    map.setBounds(bounds);
}

// 주소 검색 함수
function searchByAddress() {
    var address = document.getElementById('searchInput').value.trim();

    if (!address) {
        alert('주소를 입력해주세요.');
        return;
    }

    geocoder.addressSearch(address, function (result, status) {
        if (status === kakao.maps.services.Status.OK) {
            var centerLatLng = new kakao.maps.LatLng(result[0].y, result[0].x);
            map.setCenter(centerLatLng); // 지도 중심 이동
            map.setLevel(5); // 확대 수준 설정
            console.log(`주소 검색 성공: ${address}`, result);

            // 주소를 중심으로 영화관 검색
            searchCinemasAround(centerLatLng);
        } else {
            alert('주소 검색 결과가 없습니다.');
        }
    });
}

// 이전 마커 제거
function removeMarkers() {
    markers.forEach(function (marker) {
        marker.setMap(null);
    });
    markers = [];
}

// 버튼 클릭 이벤트 등록
document.getElementById('searchButton').addEventListener('click', function () {
    console.log('주소 검색 버튼 클릭됨');
    searchByAddress();
});
